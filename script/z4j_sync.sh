#!/bin/bash

###########################################################################

export Z4J_HOME="/home/OSSLUSER/zbx4jos"
cd $Z4J_HOME

echo "ZBX4JOS Start Sync Jobs and Job Chains"
fab --hide everything set_job_items
echo "ZBX4JOS END Sync Jobs and Job Chains"

#
