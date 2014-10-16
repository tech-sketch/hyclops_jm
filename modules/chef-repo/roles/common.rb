name "common"
description "setting HyClops JobMonitoring"
# env_run_lists "name" => ["recipe[name]"], "environment_name" => ["recipe[name::attribute]"]
# default_attributes()
# override_attributes "node" => { "attribute" => [ "value", "value", "etc." ] }
run_list([
  "recipe[selinux::disabled]"
])
