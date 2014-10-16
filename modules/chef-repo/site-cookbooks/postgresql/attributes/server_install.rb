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
default['postgresql']['log_dir'] = "#{node['postgresql']['dir']}/pg_log"

# postgresql.conf settings
default['postgresql']['config']['listen_addresses'] = 'localhost'
default['postgresql']['config']['port'] = 5432
default['postgresql']['config']['max_connections'] = 100
default['postgresql']['config']['shared_buffers'] = '256MB'
default['postgresql']['config']['work_mem'] = '16MB'
default['postgresql']['config']['maintenance_work_mem'] = '32MB'
default['postgresql']['config']['wal_level'] = 'minimal'
default['postgresql']['config']['archive_mode'] = 'off'
default['postgresql']['config']['archive_command'] = "cp %p #{node['postgresql']['archive_dir']}/%f"
default['postgresql']['config']['bytea_output'] = "hex"
default['postgresql']['config']['standard_conforming_strings'] = "on"

# pg_hba.conf settings
default['postgresql']['pg_hba'] = []
