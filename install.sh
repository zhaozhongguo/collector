#!/bin/sh

INSTALL_DIR=/opt
BASE_DIR=$(cd `dirname $0`; pwd)

mkdir -p $INSTALL_DIR/collector

cd $BASE_DIR
cp -rf bin $INSTALL_DIR/collector
cp -rf etc $INSTALL_DIR/collector
cp -rf src $INSTALL_DIR/collector

cd $INSTALL_DIR/collector
sh bin/collector.sh start
cd -

echo "\n=== finished to install collector ==="


