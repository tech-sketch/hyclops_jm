#!/bin/bash

LOG="/var/log/zabbix/zbx4jos_ext.log"
id >> $LOG
date >> $LOG
/usr/local/sbin/zbx4jos show_info >> $LOG
echo "Exit code $?" >> $LOG

##exit $?
exit 0

#
