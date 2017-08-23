#!/bin/sh

CURRENT_DIR=$(cd `dirname $0`; pwd)

if [ ! -d "$CURRENT_DIR/../log" ];then
    mkdir -p $CURRENT_DIR/../log
fi

function help_print()
{
    echo -e "----------------------------------------------\n"
    echo -e "Invalid input param !!!"
    echo -e "eg: sh collector.sh [start|stop|restart]"
    echo -e "----------------------------------------------\n"
}

function start_process()
{
    nohup python $CURRENT_DIR/../src/collector.py > /dev/null 2>&1 &
    echo -e "\n=== start success ===\n"
}

function stop_process()
{
    kill -9 `ps -ef | grep "python.*src/collector.py" | grep -v grep | awk '{print $2}'`
    echo -e "\n=== stop success ===\n"
}

function restart_process()
{
    kill -9 `ps -ef | grep "python.*src/collector.py" | grep -v grep | awk '{print $2}'`
    nohup python $CURRENT_DIR/../src/collector.py > /dev/null 2>&1 &
    echo -e "\n=== restart success ===\n"
}

case $1 in

'start')
    start_process
    ;;
'stop')
    stop_process
    ;;
'restart')
    restart_process
    ;;
*)
    help_print
    ;;
esac
