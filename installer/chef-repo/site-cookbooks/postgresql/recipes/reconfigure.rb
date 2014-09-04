#
# Cookbook Name:: postgresql
# Recipe:: reconfigure
#
# Copyright 2014, sova
#
# All rights reserved - Do Not Redistribute
#

template "#{node['postgresql']['dir']}/postgresql.conf" do
  source "postgresql.conf.erb"
  owner "postgres"
  group "postgres"
  mode 0600
end

template "#{node['postgresql']['dir']}/pg_hba.conf" do
  source "pg_hba.conf.erb"
  owner "postgres"
  group "postgres"
  mode 0600
end

service node['postgresql']['server']['service_name'] do
  action [ :restart ]
end

