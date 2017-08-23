# -*- coding: UTF-8 -*-
import os
import commands
import datetime
import traceback
import json
import time
import socket
import ConfigParser
import multiprocessing
from log import logging
from database import InfluxdbUtils




def query_active_hosts():
    """
    query all active vm hosts.
    """
    host_list = []
    try:
        #query all active vm hosts
        (status, hosts) = commands.getstatusoutput("virsh list | awk {'print $2'} | grep -v '^$'")
        if status == 0:
            hosts = hosts.split('\n')[1:]
            #query host uuid
            for host in hosts:
                (status, uuid) = commands.getstatusoutput(" ".join(["virsh dominfo ", host, "| grep 'UUID' | awk '{print $2}'"]))
                if status == 0:
                    info = {}
                    info['name'] = host
                    info['uuid'] = uuid
                    host_list.append(info)
                else:
                    continue
        else:
            logging.error("failed to query all active hosts.")
    except Exception:
        logging.error(traceback.print_exc())

    return host_list



def get_influxdb_record(host_uuid, region, obj, metric, instance, value):
    """
    Get one influxdb record.

    :param host_uuid (str) - host uuid
    :param region (str) - eg: wuxi-test-compute144
    :param obj (str) - eg: cpu/mem/disk/network
    :param metric (str) - eg: ops_write
    :param instance (str) - eg: sda1
    :param value (str) - value
    """

    return {
        "measurement": "vm_monitor_data",
        "tags": {
            "host": host_uuid,
            "region": region,
            "object": obj,
            "metric": metric,
            "instance": instance
        },
        "fields": {
            "value": float(value)
        }
    }



def write_into_influxdb(host_dict):
    """
    Wirte data into influxdb.

    :param host_dict (dict) - as blew
        {
            'name': 'instance-00000163',
            'uuid': 'dbbc272d-60b0-4380-9d23-4c011896e7f4',
            'region': 'wuxi-test-compute144',
            'client': influxdb_client
        }
    """
    host_name = host_dict['name']
    host_uuid = host_dict['uuid']
    region = host_dict['region']
    client = host_dict['client']
    db_list = []

    logging.debug("begin to collect %s data." % host_name)
    begin_time = time.time()
    try:
        prefix_cmd = "virsh qemu-agent-command " + host_name
        #query cpu stat
        (status, result) = commands.getstatusoutput(
            prefix_cmd + " '{\"execute\":\"guest-query-cpu-usage\", \"arguments\":{\"delay\":1}}'")
        if status == 0:
            result = json.loads(result)
            record = get_influxdb_record(host_uuid, region, "cpu", "usage", "total", result['return']['usage'])
            db_list.append(record)

        #query mem stat
        (status, result) = commands.getstatusoutput(
            prefix_cmd + " '{\"execute\":\"guest-query-mem-usage\"}'")
        if status == 0:
            result = json.loads(result)
            record = get_influxdb_record(host_uuid, region, "mem", "usage", "total", result['return']['usage'])
            db_list.append(record)

        #query disk stat
        (status, result) = commands.getstatusoutput(
            prefix_cmd + " '{\"execute\":\"guest-query-disk-stat\", \"arguments\":{\"delay\":1}}'")
        if status == 0:
            result = json.loads(result)
            result = result['return']['disk_stat']
            for item in result:
                record = get_influxdb_record(host_uuid, region, "disk", 'rd_ops', item['name'], item['rd_ops'])
                db_list.append(record)
                record = get_influxdb_record(host_uuid, region, "disk", 'wr_ops', item['name'], item['wr_ops'])
                db_list.append(record)
                record = get_influxdb_record(host_uuid, region, "disk", 'rd_octet', item['name'], item['rd_octet'])
                db_list.append(record)
                record = get_influxdb_record(host_uuid, region, "disk", 'wr_octet', item['name'], item['wr_octet'])
                db_list.append(record)

        #query network stat
        (status, result) = commands.getstatusoutput(
            prefix_cmd + " '{\"execute\":\"guest-query-net-stat\", \"arguments\":{\"delay\":1}}'")
        if status == 0:
            result = json.loads(result)
            result = result['return']['net_stat']
            for item in result:
                record = get_influxdb_record(host_uuid, region, "network", 'receive', item['name'], item['receive'])
                db_list.append(record)
                record = get_influxdb_record(host_uuid, region, "network", 'send', item['name'], item['send'])
                db_list.append(record)

        #write data to influxdb
        client.write(db_list)
    except Exception:
        logging.error("failed to collect %s data." % host_name)
        logging.error(traceback.print_exc())

    end_time = time.time()
    spend_time = int(end_time - begin_time)
    logging.debug("finished to collect %s data.took time: %d" % (host_name, spend_time))





def process(ip, port, interval, max_process):
    """
    Start to collect all stat and send data to db.
    :param ip (str) - influxdb ip
    :param port (int) - influxdb port
    :param interval (int) - process interval
    :param max_process (int) - process number
    """
    
    try:
        #influxdb client init
        client = InfluxdbUtils(ip, port)
        client.connect()
        client.create_retention_policy()

        while True:
            try:
                #get region
                region = socket.gethostname()

                #get all vm hosts
                hosts = query_active_hosts()
                for host in hosts:
                    host['region'] = region
                    host['client'] = client

                #process
                pool = multiprocessing.Pool(max_process)
                ret = pool.map(write_into_influxdb, hosts)
                pool.close()
                pool.join()
            except Exception:
                logging.error(traceback.print_exc())

            time.sleep(interval)
    except Exception:
        logging.error(traceback.print_exc())



def configParser():
    """
    Parser conf file.
    """
    cf = ConfigParser.ConfigParser()
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    cf.read(cur_dir + "/../etc/collector.conf")

    configs = {}
    for item in cf.items("server"):
        configs[item[0]] = item[1]

    return configs



if __name__ == '__main__':
    conf = configParser()
    process(conf['influxdb_ip'], 
        int(conf['influxdb_port']), 
        int(conf['interval']), 
        int(conf['max_process_number']))
