#
# Cookbook Name:: zabbix
# Recipe:: agent_install
#
# Copyright 2014, sova
#
# All rights reserved - Do Not Redistribute
#

include_recipe 'zabbix::rpm_install'

node[:zabbix][:agent][:packages].each do |pkg|
  yum_package pkg do
    action :install
    flush_cache [:before]
  end
end

template '/etc/zabbix/zabbix_agentd.conf' do
  source 'zabbix_agentd.conf.erb'
  owner 'zabbix'
  group 'zabbix'
  mode 0644
end

service 'zabbix-agent' do
  provider Chef::Provider::Service::Init::Redhat
  supports :status => true, :restart => true
  action [ :enable, :start ]
end
