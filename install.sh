#!/bin/sh

cd `dirname ${0}`
DIR=$PWD
INSTALL_DIR=$DIR/installer
CHEF_DIR=$INSTALL_DIR/chef-repo

# Check 64bit cpu
if [ `uname -a | grep 64 | wc -l` -ne 1 ]; then
  echo "Please install HyClops JobMonitoring on 64bit cpu."
  exit 1
fi

# Check RHEL
if [ `cat /etc/redhat-release | wc -l` -ne 1 ]; then
  echo "Please install HyClops JobMonitoring on RHEL series."
  exit 1
fi

# Chef install
if [ `rpm -q chef | wc -l` -ne 1 ]; then
  curl -L https://www.opscode.com/chef/install.sh | bash
fi

cd $CHEF_DIR
sed -i -e "s|CHEFDIR|$CHEF_DIR|g" config/solo.rb

# Install PostgreSQL9.3
if [ `rpm -qa | grep postgresql | wc -l` -eq 0 ]; then
  chef-solo -c config/solo.rb -o "role[postgresql]"
fi

# Install Zabbix 2.2
if [ `rpm -qa | grep zabbix-server | wc -l` -eq 0 ]; then
  chef-solo -c config/solo.rb -o "role[zabbix-server]"
fi

# Install JobScheduler 1.7
test -e /opt/sos-berlin.com/jobscheduler/scheduler/bin/jobscheduler.sh
if [ `echo $?` -eq 1 ]; then
  chef-solo -c config/solo.rb -o "role[jobscheduler-engine]"
fi
