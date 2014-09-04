#
# Cookbook Name:: postgresql
# Recipe:: setup_rails
#
# Copyright 2014, sova
#
# All rights reserved - Do Not Redistribute
#

production_db = 'circle_board_production'

connection_info = {
  :host => '127.0.0.1',
  :port => node['postgresql']['config']['port'],
  :username => 'postgres',
  :password => node['postgresql']['password']['postgres']
}

postgresql_database production_db do
  connection connection_info
  encoding 'utf8'
  action :create
end

postgresql_database_schema 'create schema' do
  connection connection_info
  schema_name 'cb'
  database_name production_db
  action :create
end
