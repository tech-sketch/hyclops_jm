#!/usr/bin/env python
#-*- coding: utf-8 -*

"""
	zbx4jos インストールスクリプト
	Usage : fab inst_z4j<:ユーザ名>
		・ユーザ名のデフォルトはscheduler
		・指定されたユーザ名のパスワードはユーザ名と同じ
"""


#############################################################
# インポートモジュール
#############################################################

#============================================================
# For Base
from fabric.api import lcd, cd, local, run, env, hide, sudo
import sys, os, os.path, time, fnmatch
from datetime import datetime as dt
from datetime import datetime

env.warn_only=True

env.dbuser='scheduler'
env.dbpass='scheduler'
env.dbpass2=''

env.hosts = ['127.0.0.1']
env.user = 'root'
env.password = 'password'

#============================================================

def add_user(user='scheduler',pasd='scheduler'):
	env.dbuser=user
	env.dbpass=pasd
	if env.dbuser != 'scheduler':			# ユーザ名が指定されて
		if env.dbpass == 'scheduler':		# パスワードが指定されていない
			env.dbpass=env.dbuser		# パスワードをユーザ名にする

	cmd = 'id %s' % env.dbuser
	res = sudo( cmd, user='root' )
	if res.return_code != 0:
		env.warn_only=False

		cmd = 'openssl passwd -1 %s' % env.dbpass
		res = sudo( cmd, user='root' )
		env.dbpass2 = res.replace('$', '\$')

		cmd = 'useradd %s -p"%s"' % (env.dbuser,env.dbpass2)
		local(cmd)

		env.warn_only=True

	cmd = 'id %s' % 'zbx4jos'
	res = sudo( cmd, user='root' )
	if res.return_code != 0:
		env.warn_only=False

		cmd = 'openssl passwd -1 %s' % 'zbx4jos'
		res = sudo( cmd, user='root' )
		env.dbpass2 = res.replace('$', '\$')

		cmd = 'useradd %s -p"%s"' % ('zbx4jos',env.dbpass2)
		local(cmd)

		env.warn_only=True

	cmd = 'grep %s /etc/sudoers' % env.dbuser
	res = sudo( cmd, user='root' )
	if res.return_code != 0:
		env.warn_only=False

		local('echo "%s ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers' % (env.dbuser) )

		env.warn_only=True

	cmd = 'grep %s /etc/sudoers' % 'postfix'
	res = sudo( cmd, user='root' )
	if res.return_code != 0:
		env.warn_only=False

		local('echo "postfix ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers' )

		env.warn_only=True

	cmd = 'grep zbx4jos /etc/aliases'
	res = sudo( cmd, user='root' )
	if res.return_code != 0:
		env.warn_only=False

		local('echo "zbx4jos         \\"| /usr/local/sbin/zbx4jos_mail.sh\\"" >> /etc/aliases' )

		env.warn_only=True

def inst_psql(user='scheduler',pasd='scheduler'):
	env.dbuser=user
	env.dbpass=pasd
	if env.dbuser != 'scheduler':			# ユーザ名が指定されて
		if env.dbpass == 'scheduler':		# パスワードが指定されていない
			env.dbpass=env.dbuser		# パスワードをユーザ名にする

	cmd = 'rpm -qa | grep pgdg-redhat93'
	res = sudo( cmd, user='root' )
	if res.return_code != 0:
		local('rpm -i http://yum.postgresql.org/9.3/redhat/rhel-6-x86_64/pgdg-redhat93-9.3-1.noarch.rpm')

	cmd = 'yum list installed | grep postgresql93'
	res = sudo( cmd, user='root' )
	if res.return_code != 0:
		env.warn_only=False

		local('yum -y install postgresql93-server postgresql93-devel postgresql93-contrib')
		local('service postgresql-9.3 initdb')

		local('chkconfig postgresql-9.3 on')
		local('cp pg_hba.conf /var/lib/pgsql/9.3/data/pg_hba.conf')

		env.warn_only=True

	cmd = 'service postgresql-9.3 status'
	res = sudo( cmd, user='root' )
	if res.return_code != 0:
		env.warn_only=False

		local('service postgresql-9.3 start')

		env.warn_only=True

	cmd = 'echo "create user %s createdb password \'%s\' login;"| su - postgres -c psql' % (env.dbuser,env.dbpass)
	local( cmd )

	cmd = 'grep pgsql-9.3 /etc/bashrc'
	res = sudo( cmd, user='root' )
	if res.return_code != 0:
		env.warn_only=False

		local('echo "export PATH=/usr/pgsql-9.3/bin:\$PATH" >> /etc/bashrc' )

		env.warn_only=True

	env.warn_only=False

	local( 'export PATH=/usr/pgsql-9.3/bin:$PATH;pip install psycopg2' )

	env.warn_only=True

def inst_script(user='scheduler',pasd='scheduler'):
	env.dbuser=user
	env.dbpass=pasd
	if env.dbuser != 'scheduler':			# ユーザ名が指定されて
		if env.dbpass == 'scheduler':		# パスワードが指定されていない
			env.dbpass=env.dbuser		# パスワードをユーザ名にする

	env.warn_only=False

	with lcd("script"):
		dir = '/home/%s/zbx4jos' % (env.dbuser)
		local( 'mkdir -p %s' % (dir) )
		cmd = './mov.sh %s %s' % (env.dbuser, dir)
		local( cmd )

	d = "/home/%s/sos-berlin.com/jobscheduler/%s/config/live/zbx4jos" % (env.dbuser,env.dbuser)
	local( 'mkdir -p %s' % (d) )
	local( 'chown %s.%s %s' % (env.dbuser, env.dbuser, d) )

	dir = '/home/%s/zbx4jos' % (env.dbuser)
	with lcd(dir):
		dir = '/home/%s/zbx4jos' % (env.dbuser)
		local( 'chown -R %s.%s *' % (env.dbuser, env.dbuser) )
		local( 'chmod +x *' )

	with lcd("/usr/local/sbin"):
		dir = '/home/%s/zbx4jos' % (env.dbuser)
		local( 'rm -f zbx4jos' )
		local( 'ln -s %s/zbx4jos .' % (dir) )
		local( 'rm -f zbx4jos_mail.sh' )
		local( 'ln -s %s/zbx4jos_mail.sh .' % (dir) )

	local( 'touch /var/log/zbx4jos.log' )
	local( 'chown %s.%s /var/log/zbx4jos.log' % (env.dbuser, env.dbuser) )
	local( 'chmod 0666 /var/log/zbx4jos.log*' )

	env.warn_only=True


def inst_jos(user='scheduler',pasd='scheduler'):
	env.dbuser=user
	env.dbpass=pasd
	if env.dbuser != 'scheduler':			# ユーザ名が指定されて
		if env.dbpass == 'scheduler':		# パスワードが指定されていない
			env.dbpass=env.dbuser		# パスワードをユーザ名にする

	cmd = 'su - %s -c "createdb %s"' % (env.dbuser,env.dbuser)
	local( cmd )
	cmd = 'su - %s -c "createdb zbx4jos"' % (env.dbuser)	# 空のDBを作成
	local( cmd )

	env.warn_only=False

	cmd = 'echo "alter user %s set standard_conforming_strings=off;"| su - %s -c psql' % (env.dbuser,env.dbuser)
	local( cmd )
	cmd = 'echo "alter user %s set bytea_output = \'escape\';"| su - %s -c psql' % (env.dbuser,env.dbuser)
	local( cmd )
	cmd = 'su - %s -c "createlang -U %s -l %s"' % (env.dbuser,env.dbuser,env.dbuser)
	local( cmd )

	cmd ="sed 's/OSSLUSER/%s/g' jos_inst.xml > /var/tmp/inst.xml" % (env.dbuser)
	local( cmd )

	local( 'mkdir -p /opt' )
	local( 'chmod 0777 /opt' )
	local( 'yum -y install wget' )

	env.warn_only=True

	with lcd("/var/tmp"):
		flag = os.path.exists("/var/tmp/jobscheduler_linux-x64.1.6.4043.tar.gz")

		if flag == True:
			print "ファイルは存在します"
	##		local( 'rm -f jobscheduler_linux-x64.1.6.4043.tar.gz' )
		else:
			env.warn_only=True

			local("wget http://sourceforge.net/projects/jobscheduler/files/Archive/JobScheduler%20since%201.6/jobscheduler_linux-x64.1.6.4043.tar.gz" )

			env.warn_only=False

		env.warn_only=True

		cmd = 'su - %s -c "cd /var/tmp ; tar zxf jobscheduler_linux-x64.1.6.4043.tar.gz"' % (env.dbuser)
		local( cmd )

		env.warn_only=False

	with lcd("/var/tmp/jobscheduler.1.6.4043"):
		cmd = 'su - %s -c "cd /var/tmp/jobscheduler.1.6.4043 ; ./setup.sh -u /var/tmp/inst.xml"' % (env.dbuser)
		local( cmd )

def inst_z4j(user='scheduler',pasd='scheduler'):
	env.dbuser=user
	env.dbpass=pasd
	if env.dbuser != 'scheduler':			# ユーザ名が指定されて
		if env.dbpass == 'scheduler':		# パスワードが指定されていない
			env.dbpass=env.dbuser		# パスワードをユーザ名にする

	add_user(user)
	inst_psql(user)
	inst_jos(user)
	inst_script(user)

	cmd = 'su - %s -c "cd /home/%s/zbx4jos ; zbx4jos createdb"' % (env.dbuser,env.dbuser)
	local( cmd )

	env.warn_only=False

	cmd = 'su - %s -c "cd /home/%s/zbx4jos ; zbx4jos set_job_items"' % (env.dbuser,env.dbuser)
	local( cmd )

	print( '===========================================================================================' )
	print( '実行する前に、以下の作業をしてください。' )
	print( '  1) ZABBIXサーバに外部スクリプトとしてzbx4jos_sender.shを定期的に実行するアイテムを設定をしてください。' )
	print( '===========================================================================================' )

def help():
	with hide('running','user'):
		local('fab -l')

#============================================================

