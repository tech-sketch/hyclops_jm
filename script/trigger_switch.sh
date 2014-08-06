#!/bin/bash

###########################################################################
# Set Paramaters
###########################################################################
export ZBX4JOS_HOSTID="\"10105\""
export ZBX4JOS_DESP="\"Lack of available memory on server\""
export ZBX4JOS_RULE="\"{localhost:vm.memory.size[available].last(0)}<5M\""
###########################################################################

export Z4J_HOME="/home/OSSLUSER/zbx4jos"
cd $Z4J_HOME

ZBX4JOS_HOSTID=`fab gethostid:"$1" | head -1`
echo "ZBX4JOS Start Swich Trigger rule"
## fab trigger_switch:$ZBX4JOS_HOSTID,$ZBX4JOS_DESP,$ZBX4JOS_RULE
fab trigger_switch:"$ZBX4JOS_HOSTID","Lack of available memory on server","{$1:vm.memory.size[available].last(0)}<$2M"
echo "ZBX4JOS END Swich Trigger rule"

#
