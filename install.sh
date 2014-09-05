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
  echo "Please install HyClops JobMonitoring on RHEL series OS."
  exit 1
fi

# Install fabric
yum groupinstall -y "Development Tools" "Base"
yum install -y zlib-devel tk-devel tcl-devel sqlite-devel ncurses-devel gdbm-devel readline-devel bzip2-devel db4-devel openssl-devel python-setuptools python-devel python-pip  --enablerepo=centosplus
easy_install pip virtualenv
pip install setuptools --no-use-wheel --upgrade
pip install fabric

if [ `echo $?` -ne 0 ]; then
  echo "Fabric install error occured."
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

# Install HyClops JobMonitoring
test -e /home/scheduler/zbx4jos/fabfile.py
if [ `echo $?` -eq 1 ]; then
  cd $INSTALL_DIR
  fab inst_z4j
fi
