#
# Cookbook Name:: jobscheduler
# Recipe:: user_add
#
# Copyright 2014, Suguru.Akiho
#
# All rights reserved - Do Not Redistribute
#

user node[:jobscheduler][:user] do
  home    "#{node[:jobscheduler][:user_home]}/#{node[:jobscheduler][:user]}"
  shell   "/bin/bash"
  action  :create
end

sudo node[:jobscheduler][:user] do
  name 'jobscheduler'
  nopasswd true
  user node[:jobscheduler][:user]
  defaults ['!requiretty','env_reset']
end
