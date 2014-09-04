#
# Cookbook Name:: postgresql
# Recipe:: default
#
# Copyright 2014, sova
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

file node['postgresql']['log_dir'] do
  action :delete
  not_if { ::FileTest.directory?(node['postgresql']['log_dir']) }
end

directory node['postgresql']['log_dir'] do
  user "postgres"
  group "postgres"
  mode 0744
  recursive true
  action :create
end

template "#{node['postgresql']['dir']}/postgresql.conf" do
  source "postgresql.conf.erb"
  owner "postgres"
  group "postgres"
  mode 0600
end

ruby_block 'copy original pg_hba.conf' do
  block do
    node.default[:origin_pg_hba] = node.default[:postgresql][:pg_hba]
    node.default[:postgresql][:pg_hba] = [
      {:type => 'local', :db => 'all', :user => 'postgres', :addr => nil, :method => 'trust'}
    ]
  end
end

template "#{node['postgresql']['dir']}/pg_hba.conf" do
  source "pg_hba.conf.erb"
  owner "postgres"
  group "postgres"
  mode 0600
end

execute 'Modify postgresql init script' do
  command "sed -i -e 's|/var/lib/pgsql/#{node['postgresql']['version']}|#{node['postgresql']['base_dir']}|g' /etc/init.d/postgresql-#{node['postgresql']['version']}"
  action :run
end

service node['postgresql']['server']['service_name'] do
  provider Chef::Provider::Service::Init::Redhat
  supports :status => true, :restart => true, :reload => true
  action [ :enable, :start, :reload ]
end

bash "assign-postgres-password" do
  user 'postgres'
  code <<-EOH
  echo "ALTER ROLE postgres ENCRYPTED PASSWORD '#{node['postgresql']['password']['postgres']}';" | psql -p #{node['postgresql']['config']['port']}
  EOH
  action :run
end

ruby_block 'return original pg_hba.conf' do
  block do
    node.default[:postgresql][:pg_hba] = node.default[:origin_pg_hba]
  end
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
  action [ :restart ]
end
