#
# Cookbook Name:: jobscheduler
# Recipe:: agnet_install
#
# Copyright 2014, Suguru.Akiho
#
# All rights reserved - Do Not Redistribute
#

include_recipe 'jobscheduler::user_add'

tmp_dir = Chef::Config[:file_cache_path]
tar_name = 'jobscheduler_agent.tar.gz'
mod_name = 'jobscheduler_modules'
tar_file = "#{tmp_dir}/#{tar_name}"
mod_dir = "#{tmp_dir}/jobscheduler_agent.#{node[:jobscheduler][:version][:major]}.#{node[:jobscheduler][:version][:minor]}"
js_user = node[:jobscheduler][:user]

remote_file tar_file do
  source node[:jobscheduler][:agent][:module_url]
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
  creates "#{mod_dir}/jobscheduler_agent.xml"
  action :extract_local
end

template "#{mod_dir}/jobscheduler_agent.xml" do
  source 'jobscheduler_agent.xml.erb'
  owner js_user
  group js_user
  mode 0755
end

execute 'install jobscheduler' do
  command "su scheduler -l -c '#{mod_dir}/setup.sh #{mod_dir}/jobscheduler_agent.xml > /tmp/jobscheduler_install.log'"
  not_if "ls #{node[:jobscheduler][:agent][:scheduler_home]}/#{node[:jobscheduler][:agent][:scheduler_id]}", :user => js_user
end

execute 'start jobscheduler' do
  command "su scheduler -l -c '/bin/sh #{node[:jobscheduler][:agent][:scheduler_data]}/#{node[:jobscheduler][:agent][:scheduler_id]}/bin/jobscheduler.sh start'"
  only_if { `ps ax | grep job | grep -v grep | wc -l`.to_i == 0 }
end
