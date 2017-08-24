# -*- coding: UTF-8 -*-
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
from log import logging


class InfluxdbUtils(object):
    """ 
    influxdb operator utils.
    """

    def __init__(self, 
            host=u'localhost', 
            port=8086, 
            username=u'root', 
            password=u'root', 
            dbname=u'vzhucloud'):

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.dbname = dbname

    def connect(self):
        """
        Connect to influxdb server.
        """
        self.client = InfluxDBClient(
            host=self.host, 
            port=self.port, 
            username=self.username, 
            password=self.password,
            timeout=30)

        databases = self.client.get_list_database()
        if self.dbname not in databases:
            try:
                self.client.create_database(self.dbname)
            except InfluxDBClientError:
                self.client.drop_database(self.dbname)
                self.client.create_database(self.dbname)

        self.client.switch_user(self.username, self.password)
        self.client.switch_database(self.dbname)

    def create_retention_policy(self, name=u'30days', duration='30d', replication='1'):
        """
        Create a retention policy for a database.

        :param name (str) – the name of the new retention policy
        :param duration (str) – the duration of the new retention policy. 
               Durations such as 1h, 90m, 12h, 7d, and 4w, are all supported 
               and mean 1 hour, 90 minutes, 12 hours, 7 day, and 4 weeks, respectively.
        :param replication (str) – the replication of the retention policy
        """
        ret_policies = self.client.get_list_retention_policies(self.dbname)
        for policy in ret_policies:
            if policy['name'] == name:
                return

        self.client.create_retention_policy(name, duration, replication, self.dbname, True)

    def write(self, data):
        """
        Write time series data to influxdb.

        :param data (json array) - as blew
            [{
                "measurement": "vm_monitor_data",
                "tags": {
                    "host": "5e4643d3-fab0-4adb-8a13-a9d278e28686",
                    "region": "wuxi-test-compute144",
                    "object": "disk",
                    "metric": "ops_read",
                    "instance": "/dev/sda1"
                },
                "time": "2017-03-12T22:00:00Z",
                "fields": {
                    "value": 89
                }
            }]
        """
        if not self.client.write_points(data):
            logging.error("failed to write_points.")

    def read(self, query):
        """
        Send a query to InfluxDB.

        :param query (str) -  the actual query string
        """
        return self.client.query(query)

