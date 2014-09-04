# common settings
default[:zabbix][:rpm_url] = 'http://repo.zabbix.com/zabbix/2.2/rhel/6/x86_64/zabbix-release-2.2-1.el6.noarch.rpm'

# zabbix server settings
# TODO: need to implement
default[:zabbix][:server][:host_url] = '127.0.0.1'

# zabbix agent settings
default[:zabbix][:agent][:packages] = ['zabbix-agent', 'zabbix-get', 'zabbix-sender']
default[:zabbix][:agent][:hostname] = 'Zabbix Agent'
default[:zabbix][:agent][:allow_root] = false
