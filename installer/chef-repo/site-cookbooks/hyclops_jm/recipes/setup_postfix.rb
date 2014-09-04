#
# Cookbook Name:: hyclops_jm
# Recipe:: setup_postfix
#
# Copyright 2014, TIS inc.
#
# All rights reserved - Do Not Redistribute
#

execute 'echo "zbx4jos \\"| /usr/local/sbin/zbx4jos_mail.sh\\"" >> /etc/aliases'
