name "postgresql"
description "postgresql database server"
# env_run_lists "name" => ["recipe[name]"], "environment_name" => ["recipe[name::attribute]"]
default_attributes(
  "postgresql" => {
    "enable_pgdg_yum" => true,
    "initdb_options" => "--no-locale --encoding=UTF8",
    "version" => "9.3",
    "config" => {
      "listen_addresses" => "localhost",
      "standard_conforming_strings" => "off",
      "bytea_output" => "escape"
    },
    "pg_hba" => [
      {:type => 'local', :db => 'all', :user => 'all', :addr => nil, :method => 'trust'},
      {:type => 'host', :db => 'all', :user => 'all', :addr => '127.0.0.1/32', :method => 'trust'},
      {:type => 'host', :db => 'all', :user => 'all', :addr => '::1/128', :method => 'trust'}
    ]
  }
)
# override_attributes "node" => { "attribute" => [ "value", "value", "etc." ] }
run_list(
  "recipe[postgresql::server_install]",
  "recipe[database::postgresql]"
)
