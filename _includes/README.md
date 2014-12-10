# About {#about}

HyClops JobMonitoring is the tool for system operators that is collaborating “Zabbix”(monitoring tool) and “JobScheduler”(job management tool).
This tool integrates monitoring of JobScheduler's job information on Zabbix. 

We have already released "HyClops for Zabbix" as OSS.
This tool is for monitoring Hybrid Cloud environments on Zabbix.

As next step, we focused on the "job management" feature that is insufficient on Zabbix.
JobScheduler has many advanced job management features.
But it doesn't have job monitoring features enough.
So, we developed the collaboration tool of Zabbix and JobScheduler.

This tool will lead to the reduction for the cumbersome system operations.

The collaborations of each tools are implemented by API base.
So, all original features of Zabbix and JobScheduler are available.
We don't customize any source codes(Zabbix and JobScheduler).

HyClops JobMonitoring provides following features:

* Automatically register Zabbix items for job monitoring.
* Monitor the job elapse and analyze the job elapse transition.
* Collaborate job error/delay information to Zabbix, and you can do the action based on Zabbix.
* Automatically change the Zabbix trigger threshold during job execution.

# Release Notes {#releases}

* 2014/12/10 ver.0.1.0
  * Initial release
 
# Architecture {#architecture}

![architecture]({{ site.production_url }}/assets/images/HyClopsJM_architecture.png)

HyClops JobMonitoring controls Zabbix and JobScheduler through APIs. And these are configured by Fabric scripts.
JobMonitoring uses database for Zabbix and JobScheduler APIs.
It has IP addresses, port numbers, authenticated information.

# Features detail

## Monitor the job elapse time

![architecture]({{ site.production_url }}/assets/images/job_elapse_detail.png)

JobMonitoring automatically registers the Zabbix host and item for job monitoring based on JobScheduler's job definitions.
After that, The job elapse is registered regularly in these items by JobMonitoring.
JobMonitoring registers automatically following Zabbix information.

| Auto register information in Zabbix | Description |
|--------|-----|
| Template | "Template App JobScheduler" and "Template App HyClops JM" is registered.
| Host | JobMonitoring sets the Zabbix host base on JobScheduler's process_class definition. If process_class don't be defined, JobMonitoring register the Zabbix host named "localhost".
| Item | JobMonitoring registers Zabbix items for job monitoring base on JobScheduler's job.

## Collaborate job error/delay information to Zabbix

If the job error occurred, JobMonitoring hooks mail send by JobScheduler and collaborates error flag to Zabbix.
From this, you can use Zabbix trigger and actions.

## Automatically change the Zabbix trigger threshold

![architecture]({{ site.production_url }}/assets/images/error_collaboration_detail.png)

JobMonitoring provides changing the trigger job template.
If you use this template, you can change the trigger threshold only executing the specified job.
The sample job template configures the job chain that the main job always execute if before process is failed.

# Install {#install}

## Requirements

Available OS

* CentOS 6(Verification: 6.5)

To take advantage of HyClops JobMonitoring you need to install the following middlewares to one instance.

* Zabbix (2.2 or later) (Verification: 2.2.7, 2.4.2)
* Python (2.6) (Verification: 2.6.6)
* Fabric (1.10 or later) (Verification: 1.10.0)
* PostgreSQL (9.3 or later) (Verification: 9.3.5)
* JobScheduler (1.7 or later) (Verification: 1.7.4274)

If you use [these scripts](https://github.com/tech-sketch/hyclops_jm-chef-repo), you can install automatically above middlewares.

If you install manually, you should see following pages.

* [Zabbix2.2 install manual](https://www.zabbix.com/documentation/2.2/manual/installation/install_from_packages)
* [Fabric install manual](http://www.fabfile.org/installing.html)
* [PostgreSQL install manual](http://www.postgresql.org/download/linux/redhat/)
* [JobScheduler install manual](http://www.sos-berlin.com/doc/en/scheduler_installation.pdf)

## Install HyClops JobMonitoring

you need to be a root user to do following procedure.

Download HyClops JobMonitoring modules from Github.

    Stable version.
    # curl -O https://github.com/tech-sketch/hyclops_jm/archive/[version no.].tar.gz
    # tar zxvf hyclops_jm-[version no.].tar.gz
    Latest version.
    # git clone https://github.com/tech-sketch/hyclops_jm.git

Move the package directory and modify the setting file.

    # cd hyclops_jm
    # vi hyclops_jm.conf

you need to make following settings to adapt your environment.

    # HyClops JobMonitoring user
    jm_user = hyclops_jm    # HyClops JobMonitoring OS user
    jm_passwd = hyclops_jm  # above user's password

    # JobScheduler configuration
    js_id = scheduler       # JobScheduler's scheduler id
    js_user = scheduler     # JobScheduler installed user
    js_passwd = scheduler   # above user's password
    js_host = 127.0.0.1     # JobScheduler run ip address
    js_port = 4444          # JobScheduler listen port

    # Zabbix configuration
    zbx_host = 127.0.0.1    # Zabbix run ip address
    zbx_login_user = Admin  # Zabbix Admin user name
    zbx_login_passwd = zabbix   # above user's password
    zbx_external_scripts_dir = /usr/lib/zabbix/externalscripts  # Zabbix external script directory

    # Database super user
    db_user = postgres    # PostgreSQL super user
    db_passwd =           # above user's password
    db_host = 127.0.0.1   # PostgreSQL run ip address
    db_port = 5432        # PostgreSQL listen port
    pgsql_version = 9.3   # PostgreSQL version

Run Fabric install script.

*Note: Before running fabric, you need to setting that root user login to 127.0.0.1 by ssh.*

    # fab -c hyclops_jm.conf install

After that, it will be created the HyClops JobMonitoring DB and distributed the related scripts in specify directories.

# Usage {#usage}

## Monitor the job elapse time

There is no need for setting. After a constant of time from installation, JobMonitoring registers the job monitoring items and begin monitoring by Zabbix.
If you add the job in JobScheduler, JobMonitoring register the new monitoring items automatically.

![host]({{ site.production_url }}/assets/images/zabbix_host.png)

![items]({{ site.production_url }}/assets/images/zabbix_items.png)

## Collaborate job error/delay information to Zabbix

In case of job error/delay, JobMonitoring register "1" to below item.

* jos_server_status

Setting the Zabbix trigger to above item, you can monitoring job error/delay status.

*Note: Point in initial release JobMonitoring register only "localhost" Zabbix host above status because of [issue#4](https://github.com/tech-sketch/hyclops_jm/issues/4)*

![latest_data]({{ site.production_url }}/assets/images/zabbix_latest_data.png)

## Automatically change the Zabbix trigger threshold

After installing HyClops JobMonitoring, you will find the job chain named HyClops_JM_Trigger_Switch_Template in JobScheduler's hyclops_jm directory.
This job chain is change the trigger threshold template.

![template_jobchain]({{ site.production_url }}/assets/images/jobscheduler_template_jobchain.png)

We will assume the following scenario.
In general case monitoring memory usage threshold on serverA is 20MB, but when running jobA memory usage threshold change 50MB.

![architecture]({{ site.production_url }}/assets/images/sample_jobchain.png)

In this case you should be the setting of the job chain to run a trigger change tempalte job before and after jobA is running with the following procedure.

### Copy the job tempalate

Copy the following jobs in hyclops_jm directory to serverA directory.

* HyClops_JM_Trigger_switch.job.xml
* HyClops_JM_Trigger_ret.job.xml
* target_zabbix_host.xml

### Create the job chain

Configure the job chain so as to be in the order following execution.

<pre>
(1)HyClops_JM_Trigger_switch => (2)jobA => (3)HyClops_JM_Trigger_ret
</pre>

### Configure the Zabbix host

Configure the Zabbix host named in target_zabbix_host.xml.

<pre>
&lt;params>
  &lt;!-- Configure the Zabbix host in value parameter. -->
  &lt;param name="zabbix_host" value="localhost"/>
&lt;/params>
</pre>

### Configure the before and after trigger threshold

Configure the parameter in HyClops_JM_Trigger_switch.job.xml

<pre>
&lt;params>
  &lt;include live_file="target_zabbix_host.xml" node=""/>
  &lt;!-- Specify the target of change trigger name. you select the trigger name from Zabbix Web UI. -->
  &lt;param name="trigger_name" value="Lack of available memory on server {HOST.NAME}"/>
  &lt;!-- Specify the enable of changed trigger conditional expression. *sign of inequality should be url encoded. -->
  &lt;param name="trigger_cond" value="{localhost:vm.memory.size[available].last(0)}&lt;50M"/>
&lt;/params>
</pre>

In these configuration, the Zabbix trigger threshold will be changed automatically.
The changing trigger job is executed to change the memory threshold 20MB to 50MB before JobA is started.
The recovery trigger job is executed to change the memory threshold 50MB to 20MB after JobA was executed.

# Contact {#contact}

Please send feedback to us.

[TIS Inc.](http://www.tis.co.jp)  
Strategic Technology Center

HyClops JobMonitoring Team  
<hyclops@ml.tis.co.jp>


# License {#license}

HyClops JobMonitoring is released under the Apache License, Version 2.0.
The Apache v2 full text is published at thie [link](http://www.apache.org/licenses/LICENSE-2.0).

