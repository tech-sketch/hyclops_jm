#
# Cookbook Name:: postgresql
# Recipe:: default
#
# Copyright 2014, sova
#
# All rights reserved - Do Not Redistribute
#

include_recipe 'postgresql::yum_pgdg_postgresql'

node['postgresql']['client']['packages'].each do |pg_pack|
  package pg_pack
end
