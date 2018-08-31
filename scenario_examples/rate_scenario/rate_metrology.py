#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: David PRADAS / <david.pradas@toulouse.viveris.com>

"""
Rate metrology study
"""

import sys
import argparse
from datetime import datetime
import scenario_builder as sb
from create_scenario import CreateScenario
from get_scenario import GetScenario
from modify_scenario import ModifyScenario
from start_scenario_instance import StartScenarioInstance
from status_scenario_instance import StatusScenarioInstance
from list_scenario_instances import ListScenarioInstances
from get_project import GetProject
import requests
import time
import json
import matplotlib
import matplotlib.pyplot as plt
from scipy import stats
import collect_agent
from data_access import CollectorConnection


# Scenario/project information
SCENARIO_NAME = 'Rate_Metrology'
SCENARIO_JSON_FILENAME = '{}.json'.format(SCENARIO_NAME)
SCENARIO_DESC = 'Rate metrology scenario for measuring network bandwidth'
PROJECT_NAME ='rate_jobs'
OVERRIDE = True # Override exising scenario with the same name

# Jobs configuration
CLIENT = 'client' # OpenBACH entity name of the client
SERVER = 'server' # OpenBACH entity name of the server
JOBS = ['iperf3', 'nuttcp']  # The list of job names to test (iperf3, nuttcp), default: jobs = ["iperf3"]
PARALLEL_FLOWS = [1, 5] # A list with the number of parallel flows to launch, default: parallel_flows = [1]
MTU_SIZES = [1200] # A list with the mtu sizes to test, default: mtu_sizes = [1100]
TOS_VALUES = ['0x00'] # A list wit the ToS values to test, default: tos_values = ["0x00"]
interval = 0.5 # The stats interval in seconds between the sent of stats (default 1)
iterations = 1 # Number of times you perfom the same test in order to obtain an average (min: 1)
UDP = False # True if you want to perform UDP tests 
if UDP: #FYI: UDP tests are only performed with nuttcp job
    JOBS = ['nuttcp']

udp_rate_limits = [15000000, 17000000] # min and max UDP rate to test (in b/s)
udp_rate_steps = 4000000 # in b/s
# Postprocessing information
POSTPROC = {}  # Dictionary for saving scenario information used in post-processing
POSTPROC['description'] = 'jobs instance id information for post-processing'
plot = []
colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'brown', 'gray']
markers = ['+', '.', 'x', '*', 9, 10, 5, 4]


def create_tcp_scenario():
    # Create the scenario with scenario_builder
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_DESC)

    # Constants of the OpenBACH Scenario
    scenario.add_constant('dst_ip', '192.168.1.4') # The IP of the server
    scenario.add_constant('port', '7000') # The port of the server
    if "nuttcp" in JOBS:
        scenario.add_constant('com_port', '6000') # The port of nuttcp server for signalling
    scenario.add_constant('duration', '15')# The duration of each test (sec.)
    #scenario.add_constant('tcp_eq_time', '0') # The elasped time after which we begin to consider the rate measures for TCP mean calculation

    wait_launched = []
    wait_finished = []
    wait_delay = 1
    function_id = 0
    project = GetProject()
    project.parse([PROJECT_NAME])
    p=project.execute()

    # Configure openbach functions and jobs
    for jobname in JOBS:
        for pflows in PARALLEL_FLOWS:
            for mtu in MTU_SIZES:
                for tos in TOS_VALUES:
                    for iteration in range(iterations):
                        if jobname == 'iperf3' and not UDP:
                            # Save iperf3 server information for post-processing
                            for entity_n in range(len(p.json()['entity'])):
                                if p.json()['entity'][entity_n]['name'] == SERVER:
                                    agent_name = p.json()['entity'][entity_n]['agent']['name']
                                    plot.append({'plot_name' : 'test_tcp-job_{0}-{1}flows-mtu{2}-tos{3}'.format(jobname, pflows, mtu, tos), 'job': jobname, 'id' : function_id, 'agent' : agent_name, 'iteration': iteration})
                            # Configuration of openbach functions client & server
                            launch_iperf3server = scenario.add_function(
                                'start_job_instance',
                                wait_launched=wait_launched,
                                wait_finished=wait_finished,
                                wait_delay=wait_delay
                            )
                            launch_iperf3server.configure(
                                 jobname, SERVER, offset=0,
                                 server_mode=True, port='$port', num_flows=pflows, interval = interval,
                                 exit=True
                            )
                            wait_launched = [launch_iperf3server]
                            wait_finished = []
                            wait_delay = 2
                            launch_iperf3client = scenario.add_function(
                                'start_job_instance',
                                wait_launched=wait_launched,
                                wait_finished=wait_finished,
                                wait_delay=wait_delay
                            )
                            launch_iperf3client.configure(
                                jobname, CLIENT, offset=0,
                                server_mode=False,
                                client_mode_server_ip='$dst_ip', port='$port', 
                                time='$duration', num_flows=pflows, mss=mtu-40, tos=tos 
                            )
                            wait_launched = []
                            wait_finished = [launch_iperf3client, launch_iperf3server]
                            wait_delay = 2
                            function_id = function_id + 2                        
                            
                        elif jobname == 'nuttcp':
                            if not UDP:
                                # Save nuttcp client information for post-processing
                                for entity_n in range(len(p.json()['entity'])-1):
                                    if p.json()['entity'][entity_n]['name'] == CLIENT:
                                        agent_name = p.json()['entity'][entity_n]['agent']['name']
                                        plot.append({'plot_name' : 'test_tcp-job_{0}-{1}flows-mtu{2}-tos{3}'.format(jobname, pflows, mtu, tos), 'job': jobname, 'id' : function_id+1, 'agent' : agent_name, 'iteration': iteration})
                                # Configuration of openbach functions client & server
                                launch_nuttcpserver = scenario.add_function(
                                    'start_job_instance',
                                    wait_launched=wait_launched,
                                    wait_finished=wait_finished,
                                    wait_delay=wait_delay
                                )
                                launch_nuttcpserver.configure(
                                    jobname, SERVER, offset=0,
                                    server_mode=True, command_port='$com_port', port='$port'
                                )
                                wait_launched = [launch_nuttcpserver]
                                wait_finished = []
                                wait_delay = 2
                                launch_nuttcpclient = scenario.add_function(
                                    'start_job_instance',
                                    wait_launched=wait_launched,
                                    wait_finished=wait_finished,
                                    wait_delay=wait_delay
                                )
                                launch_nuttcpclient.configure(
                                    jobname, CLIENT, offset=0,
                                    server_mode=False, server_ip='$dst_ip', command_port='$com_port', port='$port',
                                    receiver=False, dscp='{0}'.format(tos), mss=mtu-40, stats_interval = interval,
                                    duration='$duration', n_streams=pflows
                                )
                                wait_launched = []
                                wait_finished = [launch_nuttcpclient]
                                wait_delay = 2
                                stop_nuttcpserver = scenario.add_function(
                                     'stop_job_instance',
                                     wait_finished=wait_finished,
                                     wait_launched=wait_launched
                                )
                                stop_nuttcpserver.configure(launch_nuttcpserver)
                                wait_finished = [launch_nuttcpserver]
                                function_id = function_id + 3
                            else:
                                for rate in range(udp_rate_limits[0], udp_rate_limits[1], udp_rate_steps):
                                    for entity_n in range(len(p.json()['entity'])-1):
                                        if p.json()['entity'][entity_n]['name'] == CLIENT:
                                            agent_name = p.json()['entity'][entity_n]['agent']['name']
                                            plot.append({'plot_name' : 'test_udp-job_{0}-{1}flows-mtu{2}-tos{3}-rate{4}Mbps'.format(jobname, pflows, mtu, tos, rate/1000000), 'job': jobname, 'id' : function_id+1, 'agent' : agent_name, 'iteration': iteration})
                                    # Configuration of openbach functions client & server
                                    launch_nuttcpserver = scenario.add_function(
                                        'start_job_instance',
                                        wait_launched=wait_launched,
                                        wait_finished=wait_finished,
                                        wait_delay=wait_delay
                                    )
                                    launch_nuttcpserver.configure(
                                        jobname, SERVER, offset=0,
                                        server_mode=True, command_port='$com_port', port='$port'
                                    )
                                    wait_launched = [launch_nuttcpserver]
                                    wait_finished = []
                                    wait_delay = 2
                                    launch_nuttcpclient = scenario.add_function(
                                        'start_job_instance',
                                        wait_launched=wait_launched,
                                        wait_finished=wait_finished,
                                        wait_delay=wait_delay
                                    )
                                    launch_nuttcpclient.configure(
                                        jobname, CLIENT, offset=0,
                                        server_mode=False, server_ip='$dst_ip', command_port='$com_port', port='$port', udp = True,
                                        receiver=False, dscp='{0}'.format(tos), mss=mtu-40, stats_interval = interval, rate_limit = rate,
                                        duration='$duration', n_streams=pflows
                                    )
                                    wait_launched = []
                                    wait_finished = [launch_nuttcpclient]
                                    wait_delay = 2
                                    stop_nuttcpserver = scenario.add_function(
                                         'stop_job_instance',
                                         wait_finished=wait_finished,
                                         wait_launched=wait_launched
                                    )
                                    stop_nuttcpserver.configure(launch_nuttcpserver)
                                    wait_finished = [launch_nuttcpserver]
                                    function_id = function_id + 3
 

    # Update post-processing information
    POSTPROC['plot'] = plot
    scenario.write('{}.json'.format(SCENARIO_NAME)) # In case you prefer to launch the scenario from OpenBACH HMI


def save_job_id(sc_status_info):
    # Saves the job instance id of the job instances collecting data (the iperf3 server, and the nuttcp client) 
    for test in range(len(POSTPROC['plot'])):
        function_id = POSTPROC['plot'][test]['id']
        POSTPROC['plot'][test]['job_instance_id'] = sc_status_info.json()['openbach_functions'][function_id]['job']['id']

        
def plot_figure(ylabel, xlabel, title, plot_type, filename, yvalues, labels, steps=None):
    # Create/saves a matplotlib graph with the results of the scenario: a CDF and a timseries comparing all the tests
    try:
        plt.figure(figsize=(12, 8), dpi=80, facecolor='w', edgecolor='k')
    except Exception as ex:
        raise ValueError('Matplotlib problem: {}'.format(ex))
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)
    if plot_type == "cdf":
        for y_arr, label in zip(yvalues, labels):
            n, bins, patches = plt.hist(y_arr, 1000, density=1, cumulative=True, label=label)
        plt.legend()
    elif plot_type == "timeseries":
        for y_arr, label, marker, color in zip(yvalues, labels, markers, colors):
            timestamps = [i * interval for i in list(range(len(y_arr)))] # Generate the xvalues of time in seconds taking into account the interval between statistics
            plt.plot(timestamps, y_arr, label=label, color=color, marker=marker, markersize=15, linewidth=3)
        plt.legend()
    else:
        raise ValueError('Invalid plot type')
    try:
        plt.savefig(filename)
    except Exception as ex:
        raise ValueError('Error saving plot files {}'.format(ex))
    return plt

def main():
    
    #### Use of auditorium script for creating/configuring and starting the Scenario ####
    labels = []
    stat_mean_throughput = []
    stat_throughput = []
    # Check if the scenario already exists
    try:
        scenario = GetScenario()
        scenario.parse(['--project', PROJECT_NAME, SCENARIO_NAME])
        r = scenario.execute()
        r.raise_for_status()
        print('Scenario {} already exists in the project {}.'.format(SCENARIO_NAME, PROJECT_NAME))
    except requests.exceptions.HTTPError as ex:
        # if it does not exist
        if ex.response.status_code == 404:
            try:
              scenario_create_json = create_tcp_scenario()
              create_scenario = CreateScenario()
              create_scenario.parse(['--project', PROJECT_NAME, SCENARIO_JSON_FILENAME])
              r = create_scenario.execute()
              r.raise_for_status()
              print('Scenario {} has beeen successfully created in the project {}.'.format(SCENARIO_NAME, PROJECT_NAME))
            except requests.exceptions.HTTPError as ex:
                raise ValueError('Error creating scenario' + ex)
    else:
        # if it does exist
        if OVERRIDE:
            try:
                scenario_create_json = create_tcp_scenario()
                modify_scenario = ModifyScenario()
                modify_scenario.parse(['--project', PROJECT_NAME, SCENARIO_NAME, SCENARIO_JSON_FILENAME])
                r = modify_scenario.execute()
                r.raise_for_status()
                print('Scenario {} has beeen modified in the project {}.'.format(SCENARIO_NAME, PROJECT_NAME))
            except requests.exceptions.HTTPError as ex:
                 raise ValueError('Error modifying scenario' + ex)
        else:
            raise ValueError('Scenario {} already exists in the project {}'.format(SCENARIO_NAME, PROJECT_NAME))

    # Start scenario_instance and Get the scenario_instance_id
    print('# ==> Starting Scenario ...')
    start = StartScenarioInstance()
    start.parse(['--project', PROJECT_NAME, SCENARIO_NAME])
    response = start.execute(False)
    try:
        scenario_id = response.json()['scenario_instance_id']
        print("Scenario instance id: ", scenario_id)
    except KeyError as ex:
        raise KeyError('Error starting scenario instance' + ex)
    except ValueError:
        raise ValueError('Error starting scenario instance' + ex)
   
    # Save scenario id for postprocessing
    POSTPROC['scenario_id'] = scenario_id
    # Get scenario status
    status_scenario = StatusScenarioInstance()
    status_scenario.parse([str(scenario_id)])
    req_status = status_scenario.execute(False)
    status = req_status.json()['status']

    # Wait for scenario to finish
    while (status == "Scheduled" or status ==
           "Scheduling" or status == "Running"):
        time.sleep(5)
        req_status = status_scenario.execute(False)
        status = req_status.json()['status']
        print('Scenario {0} status: {1} '.format(SCENARIO_NAME, status))
    if (status == "Finished KO" or status == "Stopped"):
        raise ValueError('Error/problem during scenario')
    else:
          print("Scenario {} is finished OK".format(SCENARIO_NAME))
   
    # Get job instance ids of jobs for postprocessing
    req_status = status_scenario.execute(False)
    save_job_id(req_status)
    print('# ==> Your dictionary with the required post-processing information')
    print (json.dumps(POSTPROC, indent=4))

    #### Post-processing and plotting graphs ####
    # Connect to OpenBACH collector for retrieving data with the data access API
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/postprocess_stats/'
            'postprocess_stats_rstats_filter.conf')
    if not success:
        raise ValueError('Error connecting to OpenBACH collector')
    requester = CollectorConnection('localhost')
   
    # Import results from Collector Database using data access API
    
    for test in POSTPROC['plot']:
        if test['iteration'] == 0 and len(stat_throughput) != 0: # if the new group of iterations begins --> compute the mean over all iterations of the previous test type
             stat_mean_throughput.append([sum(t)/len(t) for t in zip(*stat_throughput)])
             labels.append(last_test)
             stat_throughput = []

        stat_name = 'throughput' if test['job'] == 'iperf3' else 'rate' #for nuttcp, the stat name is mean_rate   
        try:
            scenario, = requester.scenarios(scenario_instance_id=scenario_id, job_name=test['job'])
        except Exception as ex:
            raise ValueError('Error getting stats from collector {}'.format(ex))
             
        job_key = (test['job'], test['job_instance_id'], test['agent'])
        job_data = scenario.job_instances[job_key]
        for series in job_data.json['statistics']:
            flow = series['suffix'] # In case different flows are launched in parallel: each flow is saved with a suffix
            if test['job'] == 'nuttcp' or (test['job'] == 'iperf3' and flow == None and len(job_data.json['statistics']) > 1) or (test['job'] == 'iperf3' and len(job_data.json['statistics']) == 1 and flow == "Flow1"):
                stat_throughput.append([stat[stat_name] for stat in series['data'][0:-1]])
        if test == POSTPROC['plot'][-1]:
            stat_mean_throughput.append([sum(t)/len(t) for t in zip(*stat_throughput)])
            labels.append((test['plot_name']))
        last_test = test['plot_name']
                  
    # Plot graphs
    name_file = '{0}-id{1}'.format(SCENARIO_NAME, scenario_id)
    plt_cdf = plot_figure('CDF', 'Throughput (b/s)', 'CDF of Throughput', 'cdf',  
                    'cdf-{}.png'.format(name_file), stat_mean_throughput, labels)
    plt_throughput = plot_figure('Throughput (b/s)', 'Time (s)', 'Comparison of throughput', 'timeseries', 
                'throughput-{}.png'.format(name_file), stat_mean_throughput, labels, interval)
    plt_cdf.show()
    plt_throughput.show()
             
if __name__ == '__main__':
    main()

