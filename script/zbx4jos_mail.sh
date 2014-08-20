#!/bin/bash

DBG=0
ZBX_HOST="127.0.0.1"
ZBX_NAME="localhost"
ZBX_KEY="jos_server_status_localhost"


MAILLOG=`egrep "success|Erfolg" |grep "^Subject"`

RET=0
if [ "$MAILLOG" == "" ]
then
	RET=1
fi

if [ "$DBG" == "0" ]
then
	zabbix_sender -z $ZBX_HOST -s $ZBX_NAME -k $ZBX_KEY -o "$RET"
else
	echo zabbix_sender -z $ZBX_HOST -s $ZBX_NAME -k $ZBX_KEY -o "$RET"
fi
#
