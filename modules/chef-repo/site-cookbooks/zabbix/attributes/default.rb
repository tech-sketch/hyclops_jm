# common settings
default[:zabbix][:rpm_url] = 'http://repo.zabbix.com/zabbix/2.2/rhel/6/x86_64/zabbix-release-2.2-1.el6.noarch.rpm'

# zabbix server settings
default[:zabbix][:server][:host_url] = '127.0.0.1'
default[:zabbix][:server][:port] = '10051'
default[:zabbix][:server][:packages] = ['zabbix-server-pgsql', 'zabbix-web-pgsql', 'zabbix-web-japanese', 'zabbix-get', 'zabbix-sender']
default[:zabbix][:server][:allow_root] = false
default[:zabbix][:server][:db_host_url] = '127.0.0.1'
default[:zabbix][:server][:db_port] = 5432
default[:zabbix][:server][:db_type] = 'POSTGRESQL'
default[:zabbix][:server][:db_name] = 'zabbix'
default[:zabbix][:server][:db_user] = 'zabbix'
default[:zabbix][:server][:db_pass] = 'zabbix'
