#
# Cookbook Name:: jobscheduler
# Recipe:: engine_install
#
# Copyright 2014, Suguru.Akiho
#
# All rights reserved - Do Not Redistribute
#

include_recipe 'jobscheduler::user_add'

tmp_dir = Chef::Config[:file_cache_path]
tar_name = 'jobscheduler.tar.gz'
mod_name = 'jobscheduler_modules'
tar_file = "#{tmp_dir}/#{tar_name}"
mod_dir = "#{tmp_dir}/jobscheduler.#{node[:jobscheduler][:version][:major]}.#{node[:jobscheduler][:version][:minor]}"
js_user = node[:jobscheduler][:user]

# create database for jobscheduler
if node[:jobscheduler][:engine][:database][:type] == 'pgsql'
  connection_info = {
    :host => node[:jobscheduler][:engine][:database][:host],
    :port => node[:jobscheduler][:engine][:database][:port] || 5432,
    :username => node[:jobscheduler][:engine][:database][:root_user],
    :password => node[:jobscheduler][:engine][:database][:root_password]
  }

  postgresql_database_user node[:jobscheduler][:engine][:database][:user] do
    connection connection_info
    password node[:jobscheduler][:engine][:database][:password]
    action :create
  end

  database node[:jobscheduler][:engine][:database][:schema] do
    connection connection_info
    provider Chef::Provider::Database::Postgresql
    action :create
  end
end

remote_file tar_file do
  source node[:jobscheduler][:engine][:module_url]
  mode 0644
  owner js_user
end

directory mod_dir do
  user js_user
  group js_user
  action :create
end

tar_extract tar_file do
  user js_user
  group js_user
  target_dir tmp_dir
  creates "#{mod_dir}/jobscheduler_install.xml"
  action :extract_local
end

template "#{mod_dir}/jobscheduler_install.xml" do
  source 'jobscheduler_install.xml.erb'
  owner js_user
  group js_user
  mode 0755
end

execute 'install jobscheduler' do
  command "su scheduler -l -c '#{mod_dir}/setup.sh #{mod_dir}/jobscheduler_install.xml > /tmp/jobscheduler_install.log'"
  not_if "ls #{node[:jobscheduler][:engine][:scheduler_home]}/#{node[:jobscheduler][:engine][:scheduler_id]}", :user => js_user
end

execute 'start jobscheduler' do
  command "su scheduler -l -c '/bin/sh #{node[:jobscheduler][:engine][:scheduler_data]}/#{node[:jobscheduler][:engine][:scheduler_id]}/bin/jobscheduler.sh start'"
  only_if { `ps ax | grep job | grep -v grep | wc -l`.to_i == 0 }
end
