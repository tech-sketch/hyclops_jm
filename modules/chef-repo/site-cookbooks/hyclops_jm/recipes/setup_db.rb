#
# Cookbook Name:: hyclops_jm
# Recipe:: setup_db
#
# Copyright 2014, TIS inc.
#
# All rights reserved - Do Not Redistribute
#

if node[:hyclops_jm][:database][:type] == 'pgsql'
  sql = [
    "CREATE TABLE sysinfo (name text,value text);",
    "ALTER TABLE sysinfo OWNER TO #{node[:hyclops_jm][:database][:user]};",
    "CREATE TABLE jobid_tbl (job text,lastid text);",
    "ALTER TABLE jobid_tbl OWNER TO #{node[:hyclops_jm][:database][:user]};",
    "insert into sysinfo (name,value) values ('job_server','#{node[:hyclops_jm][:jobscheduler][:engine_url]}');",
    "insert into sysinfo (name,value) values ('job_port','#{node[:hyclops_jm][:jobscheduler][:engine_port]}');",
    "insert into sysinfo (name,value) values ('zbx_server','#{node[:hyclops_jm][:zabbix][:server_url]}');",
    "insert into sysinfo (name,value) values ('zbx_login','#{node[:hyclops_jm][:zabbix][:login_user]}');",
    "insert into sysinfo (name,value) values ('zbx_pass','#{node[:hyclops_jm][:zabbix][:login_pass]}');",
    "insert into sysinfo (name,value) values ('jos_timeout','3');"
  ]
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
    action :drop
  end

  database node[:hyclops_jm][:database][:schema] do
    connection connection_info
    provider Chef::Provider::Database::Postgresql
    action :create
    owner node[:hyclops_jm][:database][:user]
  end

  database node[:hyclops_jm][:database][:schema] do
    connection connection_info
    provider Chef::Provider::Database::Postgresql
    sql sql.join(' ')
    action :query
  end

  execute "export PATH=/usr/pgsql-#{node['postgresql']['version']}/bin:$PATH;pip install psycopg2" do
    action :run
  end
end
