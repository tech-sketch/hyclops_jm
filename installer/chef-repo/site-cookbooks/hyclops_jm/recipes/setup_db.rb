#
# Cookbook Name:: hyclops_jm
# Recipe:: setup_db
#
# Copyright 2014, TIS inc.
#
# All rights reserved - Do Not Redistribute
#

if node[:hyclops_jm][:database][:type] == 'pgsql'
  connection_info = {
    :host => node[:hyclops_jm][:database][:host],
    :port => node[:hyclops_jm][:database][:port] || 5432,
    :username => node[:hyclops_jm][:database][:root_user],
    :password => node[:hyclops_jm][:database][:root_password]
  }

  postgresql_database_user node[:hyclops_jm][:database][:user] do
    connection connection_info
    password node[:hyclops_jm][:database][:password]
    action :create
  end

  database node[:hyclops_jm][:database][:schema] do
    connection connection_info
    provider Chef::Provider::Database::Postgresql
    action :create
  end
end
