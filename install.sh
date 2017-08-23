#!/bin/sh

INSTALL_DIR=/opt
BASE_DIR=$(cd `dirname $0`; pwd)

mkdir -p $INSTALL_DIR/collector

cd $BASE_DIR
cp -rf bin $INSTALL_DIR/collector
cp -rf etc $INSTALL_DIR/collector
cp -rf src $INSTALL_DIR/collector
chmod u+x $INSTALL_DIR/collector/bin/collector.sh

mkdir -p /usr/lib/systemd/system
cp -rf collector.service /usr/lib/systemd/system
sed -i "s#INSTALL_DIR#$INSTALL_DIR#g" /usr/lib/systemd/system/collector.service

sudo /bin/systemctl daemon-reload
sudo /bin/systemctl enable collector.service
/bin/systemctl start collector.service


echo "=== success to install collector ==="
