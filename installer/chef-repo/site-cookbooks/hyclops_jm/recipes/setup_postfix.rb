#
# Cookbook Name:: hyclops_jm
# Recipe:: setup_postfix
#
# Copyright 2014, TIS inc.
#
# All rights reserved - Do Not Redistribute
#

execute 'echo "hyclops_jm \\"| /usr/local/sbin/hyclops_jm_mail.sh\\"" >> /etc/aliases'
