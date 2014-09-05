#
# Cookbook Name:: zabbix
# Recipe:: server_install
#
# Copyright 2014, TIS inc.
#
# All rights reserved - Do Not Redistribute
#

include_recipe 'zabbix::rpm_install'

node[:zabbix][:server][:packages].each do |pkg|
  yum_package pkg do
    action :install
    flush_cache [:before]
  end
end

template '/etc/zabbix/zabbix_server.conf' do
  source 'zabbix_server.conf.erb'
  owner 'zabbix'
  group 'zabbix'
  mode 0644
end

template '/etc/zabbix/web/zabbix.conf.php' do
  source 'zabbix.conf.php.erb'
  owner 'zabbix'
  group 'zabbix'
  mode 0644
end

bash 'execute initial sql' do
  user "postgres"
  code <<-EOH
  createuser zabbix -U postgres
  createdb -U postgres -O zabbix zabbix
  psql -U zabbix zabbix < /usr/share/doc/zabbix-server-pgsql-2.2.*/create/schema.sql
  psql -U zabbix zabbix < /usr/share/doc/zabbix-server-pgsql-2.2.*/create/images.sql
  psql -U zabbix zabbix < /usr/share/doc/zabbix-server-pgsql-2.2.*/create/data.sql
  sed -i -e "s|# php_value date.timezone Europe/Riga|php_value date.timezone Asia/Tokyo|" /etc/httpd/conf.d/zabbix.conf
  EOH
end

service 'zabbix-server' do
  provider Chef::Provider::Service::Init::Redhat
  supports :status => true, :restart => true
  action [ :enable, :start ]
end

service 'httpd' do
  provider Chef::Provider::Service::Init::Redhat
  supports :status => true, :restart => true
  action [ :enable, :start ]
end
