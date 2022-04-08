# Auditorium Scripts

The auditorium-scripts can be used as standalone scripts or included as a Python module. Contrary to
the [Auditorium Web Interface][1], these scripts matches all OpenBACH capabilities and offers more
power to the users and the administrators.

Keep in mind that the multi-users restrictions of OpenBACH also apply to theses scripts; so a simple
user won't be able to use administrator commands.

Please refer to the [Introduction to OpenBACH-extra and OpenBACH API](/apis/README.md) page to see how
to install and set up your platform to use the API described in this page. 

## Available scripts

The available scripts are listed below:

```
add_collector.py
add_job.py
add_project.py
assign_collector.py
change_collector_address.py
create_scenario.py
del_collector.py
del_job.py
del_project.py
del_scenario_instance.py
del_scenario_instances.py
del_scenario.py
get_collector.py
get_job_help.py
get_job_stats.py
get_project.py
get_scenario.py
install_agent.py
install_jobs.py
kill_all.py
list_agents.py
list_collectors.py
list_installed_jobs.py
list_job_instances.py
list_jobs.py
list_projects.py
list_scenario_instances.py
list_scenarios.py
modify_agent.py
modify_collector.py
modify_project.py
modify_scenario.py
open_logs.py
push_file.py
restart_job_instance.py
set_agent_log_severity.py
set_job_log_severity.py
set_job_stat_policy.py
start_job_instance.py
start_scenario_instance.py
state_agent.py
state_collector.py
state_job_instance.py
state_job.py
state_push_file.py
status_job_instance.py
status_scenario_instance.py
stop_job_instance.py
stop_scenario_instance.py
uninstall_agent.py
uninstall_jobs.py
```

> :warning: You can import the classes of auditorium-scripts from any directory, but the
file "controller" (with the controller IP/login/password) should be in the directory from
which you launch your scripts in order to correctly access the controller.

## How to launch the scripts in your terminal shell

The following example shows how to launch the `fping` job with different arguments:

```
python3 start_job_instance.py **admin_ip** fping -a destination_ip **dest_ip** -a count 2 -a interval 10
```

For more complex scenarios, sub commands may be needed. 
The following example shows how to set up an iperf3 server and iperf3 client.

On the server: 
```
python3 start_job_instance.py **srv_admin_ip** iperf3 -a num_flows 2 -s server
```

On the client:
```
python3 start_job_instance.py **clt_admin_ip** iperf3 -a num_flows 2 -s client server_ip **srv_data_ip** -s client duration_time 60 --sub-sub-command client udp bandwidth 20M
```

## Importing the scripts in your Python files

Alternatively, they each host a class that you can import for scripting purposes. _e.g._:

``` python
# This script installs the job iperf3 in the agent '172.20.34.41'

from auditorium_scripts.install_jobs import InstallJobs

def main():
    install_jobs = InstallJobs()
    install_jobs.parse('-j iperf3 -a 172.20.34.41'.split())
    install_jobs.execute()

if __name__ == '__main__':
    main()
```


[1]: https://github.com/CNES/openbach/blob/master/src/auditorium/README.md
