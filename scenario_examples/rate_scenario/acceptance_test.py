#!/usr/bin/env python3

import itertools

import matplotlib.pyplot as plt
from scenario_observer import ScenarioObserver

import scenario_builder as sb


SCENARIO_NAME = 'Metrology FAIRNESS TRANSPORT'
SCENARIO_DESCRIPTION = 'This scenario aims at comparing the fairness and performance of two congestion controls for different SATCOM system characteristics.'
UDP_RATES = range(10000, 17000, 4000)
NUTTCP_CLIENT_UDP_LABEL = 'nuttcp client: {} flows, rate {}, mtu {}b, tos {} (iter {})'
NUTTCP_SERVER_UDP_LABEL = 'nuttcp server: {} flows, rate {}, mtu {}b, tos {} (iter {})'
CLIENT_TCP_LABEL = '{} client: {} flows, mtu {}, tos {} (iter {})'
SERVER_TCP_LABEL = '{} server: {} flows, mtu {}, tos {} (iter {})'
PROJECT_NAME = 'rate_jobs'
POST_PROC = []

def build_metrics_scenario(
        client_entity, server_entity):
    
    # Create the scenario with scenario_builder
    scenario = sb.Scenario('metrics', SCENARIO_DESCRIPTION)
    scenario.add_argument('dst_ip', '192.168.19.3') # The IP of the server
    scenario.add_argument('port', '7000') # The port of the server
    scenario.add_constant('com_port', '6000') # The port of nuttcp server for signalling
    scenario.add_constant('duration', '10') # The duration of each test (sec.)

    # Configure/Launch nuttcp 

    launch_nuttcpserver = scenario.add_function(
            'start_job_instance'
    )
    launch_nuttcpserver.configure(
            'nuttcp', server_entity, offset=0,
            command_port='$com_port', server={}
    )
    launch_nuttcpclient = scenario.add_function(
            'start_job_instance',
            wait_launched=[launch_nuttcpserver],
            wait_delay=2,
    )
    launch_nuttcpclient.configure(
            'nuttcp', client_entity, offset=0,
            command_port='$com_port', client = {'server_ip':'$dst_ip',
           'port':'$port', 'receiver':'{0}'.format(False), 
           'duration':'$duration', 'rate_limit':'{0}'.format('10M'), 'udp':{}}
    )
    stop_nuttcpserver = scenario.add_function(
           'stop_job_instance',
            wait_finished=[launch_nuttcpclient],
    )
    stop_nuttcpserver.configure(launch_nuttcpserver)

    # Job 'owamp-server'
    owamp_server = scenario.add_function('start_job_instance',
            wait_launched = [stop_nuttcpserver])

    owamp_server.configure('owamp-server', server_entity, offset=0,
            server_address='$dst_ip')

    # Job 'owamp-client'
    owamp_client = scenario.add_function('start_job_instance',
            wait_launched=[owamp_server],
            wait_delay=5)
    owamp_client.configure('owamp-client', client_entity, offset=0,
            destination_address='$dst_ip')

    stop_pings = scenario.add_function('stop_job_instance',
            wait_finished=[owamp_client])
    
    stop_pings.configure(owamp_server)

    return scenario

def build_rate_scenario(
           client_entity, server_entity):
   
    scenario = sb.Scenario('File', SCENARIO_DESCRIPTION)
    scenario.add_argument('dst_ip', 'The IP of the iperf3 server') # The IP of the server
    scenario.add_argument('port', 'The port of the iperf3 server') # The port of the server
    scenario.add_argument('cc_servera', 'Congestion Control of server A')
    #scenario.add_argument('cc_serverb', 'Congestion Control of server B')


    launch_sysctlservera = scenario.add_function(
           'start_job_instance',
           label='sysctl_servera',
    )
    
    launch_sysctlservera.configure(
           'sysctl', server_entity,
            parameter='net.ipv4.tcp_available_congestion_control', value='$cc_servera',
    )
    
    #launch_sysctlserverb.configure(
    #       parameter='net.ipv4.tcp_available_congestion_control', value='cc_serverb',
    #)

    launch_iperf3server = scenario.add_function(
           'start_job_instance',
           label='iperf3_server',
           wait_finished=[launch_sysctlservera],
           wait_delay=2,
    )
    launch_iperf3server.configure(
           'iperf3', server_entity, offset=0, port='$port',
           server = {'exit':True}
    )
    launch_iperf3client = scenario.add_function(
           'start_job_instance',
           wait_launched=[launch_iperf3server],
           wait_delay=2,
           label='iperf3_client',
    )
    launch_iperf3client.configure(
           'iperf3', client_entity, offset=0,
           port='$port', client = {'server_ip':'$dst_ip',
           'transmitted_size':'100M', 'tcp':{}}
    )
    wait_finished = [launch_iperf3client, launch_iperf3server]

    return scenario


def build_main_scenario(
    client_entity, server_entity, project_name):
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_DESCRIPTION)

    metrics_sce = build_metrics_scenario(client_entity, server_entity)
    metrics_sce.write('metrics.json')
    observer1 = ScenarioObserver(metrics_sce.name, project_name, metrics_sce)
    rate_sce = build_rate_scenario(client_entity, server_entity)
    observer2 = ScenarioObserver(rate_sce.name, project_name, rate_sce)
    rate_sce.write('rate.json')
    
    metrics_sub = scenario.add_function(
          'start_scenario_instance',
    )
    metrics_sub.configure(
          metrics_sce.name,
          dst_ip='192.168.19.3',
          port=7000,
    )

    rate_sub = scenario.add_function(
          'start_scenario_instance',
          wait_finished=[metrics_sub],
          wait_delay=2,
    )
    rate_sub.configure(
          rate_sce.name,
          dst_ip='192.168.19.3',
          port=7000,
          cc_servera='cubic',
          #cc_serverb='cubic',
    )
    rate_sub2 = scenario.add_function(
          'start_scenario_instance',
          wait_finished=[rate_sub],
          wait_delay=2,
    )
    rate_sub2.configure(
          rate_sce.name,
          dst_ip='192.168.19.3',
          port=7000,
          cc_servera='cubic',
          #cc_serverb='cubic',
    )   
    return scenario

def main(project_name):
    #Build a scenario specifying the entity name of the client and the server.
    scenario_builder = build_main_scenario('client', 'client2', project_name)
    #scenario_builder.write('your_scenario.json')
    
    observer = ScenarioObserver(SCENARIO_NAME, project_name, scenario_builder)
    observer.launch_and_wait()


if __name__ == '__main__':
    main('rate_jobs')
