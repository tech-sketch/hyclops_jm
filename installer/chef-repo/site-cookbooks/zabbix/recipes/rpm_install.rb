#
# Cookbook Name:: zabbix
# Recipe:: rpm_install
#
# Copyright 2014, sova
#
# All rights reserved - Do Not Redistribute
#

repo_rpm = "#{Chef::Config[:file_cache_path]}/zabbix_repo.rpm"

remote_file repo_rpm do
  source node[:zabbix][:rpm_url]
end

rpm_package repo_rpm do
  action :install
end
