#!/usr/bin/env python
#-*- coding: utf-8 -*

"""
  HyClop JobMonitoring install script
  Usage : fab install<:username>
    - Default user is scheduler
"""

#############################################################
# Import modules and initial settings
#############################################################
from fabric.api import lcd, cd, local, run, env, hide, sudo
import sys, os, os.path, time, fnmatch
from datetime import datetime as dt
from datetime import datetime

env.hosts = ['127.0.0.1']

#============================================================
# private functions
#============================================================
def _set_user(user, passwd):
  env.jm_user = user
  env.jm_passwd = passwd

def _allow_error():
  env.warn_only = True

def _deny_error():
  env.warn_only = False

#============================================================
# public functions
#============================================================
def add_user(user, passwd):
  # Add hyclops jm user
  _allow_error()
  res = run('id %s' % user)
  _deny_error()
  if res.return_code != 0:
    local('useradd %s -p"%s"' %(user, passwd))

def sudo_to_user(user):
  _allow_error()
  res = run('grep %s /etc/sudoers || grep -r %s /etc/sudoers.d' % (user, user))
  _deny_error()
  if res.return_code != 0:
    local('echo "%s  ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/%s' % (user, user))
    local('echo "Defaults:%s !requiretty,env_reset" >> /etc/sudoers.d/%s' % (user, user))


def setup_postfix():
  _allow_error()
  res = run('grep hyclops_jm /etc/aliases')
  _deny_error()
  if res.return_code != 0:
    local('echo "hyclops_jm: | \\"/usr/local/sbin/hyclops_jm_mail.sh\\"" >> /etc/aliases')
    local('newaliases')

def setup_db():
  local("export PATH=/usr/pgsql-%s/bin:$PATH;pip install psycopg2" % env.pgsql_version)

  sqls = ["create table sysinfo (name text,value text);",
    "alter table sysinfo owner to %s;" % env.js_user,
    "create table jobid_tbl (job text,lastid text);",
    "alter table jobid_tbl owner to %s;" % env.js_user,
    "insert into sysinfo (name,value) values ('job_server','%s');" % env.js_host,
    "insert into sysinfo (name,value) values ('job_port','%s');" % env.js_port,
    "insert into sysinfo (name,value) values ('zbx_server','%s');" % env.zbx_host,
    "insert into sysinfo (name,value) values ('zbx_login','%s');" % env.zbx_login_user,
    "insert into sysinfo (name,value) values ('zbx_pass','%s');" % env.zbx_login_passwd,
    "insert into sysinfo (name,value) values ('jos_timeout','3');"]
  psql = "psql -U %s -h %s -p %s -c" % (env.db_user, env.db_host, env.db_port)

  _allow_error()
  local("%s 'drop database %s'" % (psql, env.jm_user))
  _deny_error()
  local("%s 'create database %s owner = %s'" % (psql, env.jm_user, env.js_user))

  for sql in sqls:
    psql = "psql -U %s -h %s -p %s -d %s -c" % (env.db_user, env.db_host, env.db_port, env.jm_user)
    local("%s \"%s\"" % (psql, sql))

def setup_scripts():
  log_dir = '/var/log/hyclops_jm'
  jm_home = "/home/%s/hyclops_jm" % env.js_user
  js_data = "/home/%s/sos-berlin.com/jobscheduler/%s" % (env.js_user, env.js_id)

  local("mkdir -p %s" % log_dir)
  local("mkdir -p %s/live" % jm_home)
  local("sed 's/HYCLOPS_JM_USER/%s/g' modules/scripts/fabfile.py > %s/fabfile.py" % (env.js_user, jm_home))
  local("chown -R %s:%s %s" % (env.js_user, env.js_user, log_dir))
  local("chown -R %s:%s %s" % (env.js_user, env.js_user, jm_home))
  local("sed 's/HYCLOPS_JM_USER/%s/g' modules/scripts/hyclops_jm > /usr/local/sbin/hyclops_jm" % env.js_user)
  local("sed 's/HYCLOPS_JM_USER/%s/g' modules/scripts/hyclops_jm_mail.sh > /usr/local/sbin/hyclops_jm_mail.sh" % env.js_user)
  local("chown %s:%s /usr/local/sbin/hyclops_jm*" % (env.js_user, env.js_user))
  local("chmod +x /usr/local/sbin/hyclops_jm*")

  local("mkdir -p %s/config/live/hyclops_jm" % js_data)
  local("chown %s:%s %s/config/live/hyclops_jm" % (env.js_user, env.js_user, js_data))
  files = local("cd modules; find live -type f", capture=True)
  for file in files.split('\n'):
    local("sed 's/HYCLOPS_JM_USER/%s/g' modules/%s > %s/config/%s" % (env.js_user, file, js_data, file))

def install(user = 'hyclops_jm', passwd = 'hyclops_jm'):
  if 'js_user' not in env:
    print 'Usage: fab -c hyclops_jm.conf install'
    return False

  _deny_error()
  _set_user(user, passwd)

  add_user(user, passwd)
  add_user(env.js_user, env.js_passwd)
  sudo_to_user(env.js_user)
  setup_postfix()
  setup_db()
  setup_scripts()

  print "================================================="
  print "= Installing HyClops JM is completed!!          = "
  print "= You go to next step.                          = "
  print "= - Access the Zabbix web interface.            = "
  print "=   - example: http://your-domain/zabbix        = "
  print "= - Create Host name [localhost]                = "
  print "= - Import Template and attach to localhost     = "
  print "= - So you can get HyClops JM functions!!       = "
  print "================================================="
