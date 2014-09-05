#!/bin/sh

cd `dirname ${0}`
DIR=$PWD
INSTALL_DIR=$DIR/installer
CHEF_DIR=$INSTALL_DIR/chef-repo

USER=scheduler
JM_HOME=/home/$USER/hyclops_jm
JS_DATA=/home/$USER/sos-berlin.com/jobscheduler/$USER

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
pip install setuptools --upgrade
pip install fabric --upgrade

if [ `echo $?` -ne 0 ]; then
  echo "Fabric install error occured."
  exit 1
fi

# Chef install
rpm -q chef
if [ `echo $?` -ne 0 ]; then
  curl -L https://www.opscode.com/chef/install.sh | bash
  if [ `echo $?` -ne 0 ]; then
    echo "Chef install error occured."
    exit 1
  fi
fi

cd $CHEF_DIR
sed -i -e "s|CHEFDIR|$CHEF_DIR|g" config/solo.rb

# Install PostgreSQL9.3
if [ `rpm -qa | grep postgresql | wc -l` -eq 0 ]; then
  chef-solo -c config/solo.rb -o "role[postgresql]"
  if [ `echo $?` -ne 0 ]; then
    echo "PostgreSQL install error occured."
    exit 1
  fi
fi

# Install Zabbix 2.2
if [ `rpm -qa | grep zabbix-server | wc -l` -eq 0 ]; then
  chef-solo -c config/solo.rb -o "role[zabbix-server]"
  if [ `echo $?` -ne 0 ]; then
    echo "Zabbix install error occured."
    exit 1
  fi
fi

# Install JobScheduler 1.7
test -e /opt/sos-berlin.com/jobscheduler/scheduler/bin/jobscheduler.sh
if [ `echo $?` -eq 1 ]; then
  chef-solo -c config/solo.rb -o "role[jobscheduler-engine]"
  if [ `echo $?` -ne 0 ]; then
    echo "JobScheduler install error occured."
    exit 1
  fi
fi

# Install HyClops JobMonitoring
test -e /home/scheduler/hyclops_jm/fabfile.py
if [ `echo $?` -eq 1 ]; then
  cd $INSTALL_DIR
  LOG_DIR=/var/log/hyclops
  mkdir -p $LOG_DIR
  mkdir -p $JM_HOME
  mkdir -p $JM_HOME/live
  sed 's/HYCLOPS_JM_USER/'$USER'/g' script/fabfile.py > $JM_HOME/fabfile.py
  chown -R $USER:$USER $JM_HOME
  chown -R $USER:$USER $LOG_DIR
  sed 's/HYCLOPS_JM_USER/'$USER'/g' script/hyclops_jm > /usr/local/sbin/hyclops_jm
  sed 's/HYCLOPS_JM_USER/'$USER'/g' script/hyclops_jm_mail.sh > /usr/local/sbin/hyclops_jm_mail.sh
  chown $USER:$USER /usr/local/sbin/hyclops_jm*
  chmod +x /usr/local/sbin/hyclops_jm*

  mkdir $JS_DATA/config/live/hyclops_jm
  chown $USER:$USER $JS_DATA/config/live/hyclops_jm
  for f in `find live -type f`
  do
    sed 's/HYCLOPS_JM_USER/'$USER'/g' $f > $JS_DATA/config/$f
  done
fi
if [ `echo $?` -ne 0 ]; then
  echo "HyClops JM install error occured."
  exit 1
fi
echo "================================================="
echo "= Installing HyClops JM is completed!!          = "
echo "= You go to next step.                          = "
echo "= - Access the Zabbix web interface.            = "
echo "=   - example: http://your-domain/zabbix        = "
echo "= - Create Host name [localhost]                = "
echo "= - Import Template and attach to localhost     = "
echo "= - So you get HyClops JM functions!!           = "
echo "================================================="
