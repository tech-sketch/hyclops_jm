# service settings
default['postgresql']['version'] = '9.3'
default['postgresql']['client']['packages'] = ["postgresql#{node['postgresql']['version'].split('.').join}-devel"]
default['postgresql']['server']['packages'] = ["postgresql#{node['postgresql']['version'].split('.').join}-server"]
default['postgresql']['contrib']['packages'] = ["postgresql#{node['postgresql']['version'].split('.').join}-contrib"]
default['postgresql']['base_dir'] = "/var/lib/pgsql/#{node['postgresql']['version']}"
default['postgresql']['dir'] = "#{node['postgresql']['base_dir']}/data"
default['postgresql']['server']['service_name'] = "postgresql-#{node['postgresql']['version']}"
default['postgresql']['initdb_options'] = ''
default['postgresql']['archive_dir'] = "#{node['postgresql']['base_dir']}/wal_archive"
default['postgresql']['log_dir'] = '/var/log/pgsql'

# postgresql.conf settings
default['postgresql']['config']['listen_addresses'] = 'localhost'
default['postgresql']['config']['port'] = 5432
default['postgresql']['config']['max_connections'] = 100
default['postgresql']['config']['shared_buffers'] = '1GB'
default['postgresql']['config']['work_mem'] = '16MB'
default['postgresql']['config']['maintenance_work_mem'] = '32MB'
default['postgresql']['config']['wal_level'] = 'archive'
default['postgresql']['config']['archive_mode'] = 'on'
default['postgresql']['config']['archive_command'] = "cp %p #{node['postgresql']['archive_dir']}/%f"

# pg_hba.conf settings
default['postgresql']['pg_hba'] = [
  {:type => 'local', :db => 'all', :user => 'all', :addr => nil, :method => 'md5'},
  {:type => 'host', :db => 'all', :user => 'all', :addr => '127.0.0.1/32', :method => 'md5'},
  {:type => 'host', :db => 'all', :user => 'all', :addr => '::1/128', :method => 'md5'}
]
