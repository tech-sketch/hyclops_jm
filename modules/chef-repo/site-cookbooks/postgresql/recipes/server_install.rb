#
# Cookbook Name:: postgresql
# Recipe:: server_install
#
# Copyright 2014, TIS inc.
#
# All rights reserved - Do Not Redistribute
#

include_recipe 'postgresql::client'

node['postgresql']['server']['packages'].each do |pg_pack|
  package pg_pack
end

node['postgresql']['contrib']['packages'].each do |pg_pack|
  package pg_pack
end

node['postgresql']['server']['packages'].each do |pg_pack|
  package pg_pack
end

directory node['postgresql']['archive_dir'] do
  user "postgres"
  group "postgres"
  mode 0744
  recursive true
  action :create
end

directory node['postgresql']['dir'] do
  user "postgres"
  group "postgres"
  mode 0700
  recursive true
  action :create
end

execute "su -l postgres -c '/usr/pgsql-#{node['postgresql']['version']}/bin/initdb -D #{node['postgresql']['dir']} #{node['postgresql']['initdb_options']}'" do
  not_if { ::FileTest.exist?(File.join(node['postgresql']['dir'], "PG_VERSION")) }
end

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
  provider Chef::Provider::Service::Init::Redhat
  supports :status => true, :restart => true, :reload => true
  action [ :enable, :start, :reload ]
end
