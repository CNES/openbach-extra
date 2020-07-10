#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2019 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#  Author: Nicolas Kuhn / <nicolas.kuhn@cnes.fr>

"""
This script is part of the OpenBACH validation suite. 
This script can run all available executors - or a sub set of them
The available entities are :

+------------+    +---------------+    +------------+    +-------------+
|wss_admin_ip|    |midbox_admin_ip|    |wsc_admin_ip|    |ctrl_admin_ip|
+------------+    +---------------+    +------------+    +-------------+
|entity:     |    |entity:        |    |entity:     |    |             | 
| wss        |    | midbox        |    |  wsc       |    |             |
+------------+    +---------------+    +------------+    +-------------+
|      wss_ip|    |midbox_ip_wss  |    |            |    |             |
|      wss_if|    |midbox_if_wss  |    |            |    |             |
|            |    |  midbox_ip_wsc|    |wsc_ip      |    |             |
|            |    |  midbow_if_wsc|    |wsc_if      |    |             |
+------------+    +---------------+    +------------+    +-------------+

Using parameters, the script has the following options:
    - all : all the available executors will be tested
    - network : all the executor_network_* will be tested
    - transport : all the executor_transport_* will be tested
    - service : all the executor_service_* will be tested
"""

from auditorium_scripts.scenario_observer import ScenarioObserver, DataProcessor
from scenario_builder.scenarios import network_configure_link, network_delay, network_global, network_jitter, network_one_way_delay, network_qos, network_rate, service_data_transfer, service_ftp, service_traffic_mix, service_video_dash, service_voip, service_web_browsing, transport_tcp_one_flow, transport_tcp_stack_conf

def main(argv=None):
    observer = ScenarioObserver()
    # entity arguments
    observer.add_scenario_argument(
            '--midbox-entity', '-m', required=True,
            help='Name of the midbox entity')
    observer.add_scenario_argument(
            '--wss', '-s', required=True,
            help='Name of the WSS entity')
    observer.add_scenario_argument(
            '--wsc', '-c', required=True,
            help='Name of the WSC entity')
    observer.add_scenario_argument(
            '--post-processing-entity',
            help='Name of the entity where the post-processing jobs should run')
    observer.add_scenario_argument(
            '--tested-executor', '--t-e', required=True,
            help='available executors that will be tested'
            'all, network, transport, service'
            )
    # network setup arguments
    observer.add_scenario_argument(
            '--bandwidth-wss-to-wsc', '-B', required=True,
            help='Bandwidth allocated for the server to answer the client')
    observer.add_scenario_argument(
            '--bandwidth-wsc-to-wss', '-b', required=True,
            help='Bandwidth allocated for the client to ask the server')
    observer.add_scenario_argument(
            '--delay-wss-to-wsc', '-D', required=True, type=int,
            help='Delay for a packet to go from the server to the client')
    observer.add_scenario_argument(
            '--delay-wsc-to-wss', '-d', required=True, type=int,
            help='Delay for a packet to go from the client to the server')
    observer.add_scenario_argument(
            '--loss-wss-to-wsc', '-L', required=True,
            help='Loss for a packet to go from the server to the client')
    observer.add_scenario_argument(
            '--loss-wsc-to-wss', '-l', required=True,
            help='Loss for a packet to go from the client to the server')
    # address - interfaces arguments
    observer.add_scenario_argument(
            '--wss-ip', '-I', required=True,
            help='IP of WSS')
    observer.add_scenario_argument(
            '--wsc-ip', '-i', required=True,
            help='IP of WSC')
    observer.add_scenario_argument(
            '--middlebox-interface-wss', '--midbox-if-wss', required=True,
            help='Middlebox interface on the WSS network')
    observer.add_scenario_argument(
            '--middlebox-interface-wsc', '--midbox-if-wsc', required=True,
            help='Middlebox interface on the WSC network')
    # executors arguments
    observer.add_scenario_argument(
            '--port', '-p', default=5201, type=int,
            help='Port used for the data transfer')
    observer.add_scenario_argument(
            '--file-size', '--size', '-f',
            help='Size of the file transfer')
    observer.add_scenario_argument(
            '--duration', default=10, type=int,
            help='Duration of the file transfer')
    args = observer.parse(argv)

    l_tested_executors = []
       
    # executor_network_configure_link
    l_tested_executors.append('executor_network_configure_link')
    print('executor_network_configure_link')
    scenario = network_configure_link.build(
            args.midbox_entity,
            args.middlebox_interface_wsc,
            'egress',
            'clear',
            args.bandwidth_wss_to_wsc,
            args.delay_wss_to_wsc,
            0,
            'random',
            args.loss_wss_to_wsc)
    #observer.launch_and_wait(scenario)
    scenario = network_configure_link.build(
            args.midbox_entity,
            args.middlebox_interface_wss,
            'egress',
            'clear',
            args.bandwidth_wsc_to_wss,
            args.delay_wsc_to_wss,
            0,
            'random',
            args.loss_wss_to_wsc)
    #observer.launch_and_wait(scenario)
    scenario = network_configure_link.build(
            args.midbox_entity,
            args.middlebox_interface_wsc,
            'egress',
            'apply',
            args.bandwidth_wss_to_wsc,
            args.delay_wss_to_wsc,
            0,
            'random',
            args.loss_wss_to_wsc)
    #observer.launch_and_wait(scenario)
    scenario = network_configure_link.build(
            args.midbox_entity,
            args.middlebox_interface_wss,
            'egress',
            'apply',
            args.bandwidth_wsc_to_wss,
            args.delay_wsc_to_wss,
            0,
            'random',
            args.loss_wss_to_wsc)
    #observer.launch_and_wait(scenario)

    # access 
    if args.tested_executor in ['access','all']:
        print('Testing access executors')

    # network 
    if args.tested_executor in ['network','all']:
        print('Testing network executors')
    
        # executor_network_delay
        l_tested_executors.append('executor_network_delay')
        print('executor_network_delay')
        
        # executor_network_global
        l_tested_executors.append('executor_network_global')
        print('executor_network_global')
        
        # executor_network_jitter
        l_tested_executors.append('executor_network_jitter')
        print('executor_network_jitter')
        
        # executor_network_one_way_delay
        l_tested_executors.append('executor_network_one_way_delay')
        print('executor_network_one_way_delay')
        
        # executor_network_qos
        l_tested_executors.append('executor_network_qos')
        print('executor_network_qos')
        
        # executor_network_rate
        l_tested_executors.append('executor_network_rate')
        print('executor_network_rate')

    # transport 
    if args.tested_executor in ['transport','all']:
        print('Testing transport executors')
        
        # executor_transport_tcp_stack_conf
        l_tested_executors.append('executor_transport_tcp_stack_conf')
        print('executor_transport_tcp_stack_conf')
        
        # executor_transport_tcp_one_flow
        l_tested_executors.append('executor_transport_tcp_one_flow')
        print('executor_transport_tcp_one_flow')

    # service 
    if args.tested_executor in ['service','all']:
        print('Testing service executors')
        
        # executor_service_data_transfer
        l_tested_executors.append('executor_service_data_transfer')
        print('executor_service_data_transfer')
        
        # executor_service_ftp
        l_tested_executors.append('executor_service_ftp')
        print('executor_service_ftp')
        
        # executor_service_traffic_mix
        l_tested_executors.append('executor_service_traffic_mix')
        print('executor_service_traffic_mix')
        
        # executor_service_video_dash
        l_tested_executors.append('executor_service_video_dash')
        print('executor_service_video_dash')
        
        # executor_service_voip
        l_tested_executors.append('executor_service_voip')
        print('executor_service_voip')
        
        # executor_service_web_browsing
        l_tested_executors.append('executor_service_web_browsing')
        print('executor_service_web_browsing')

    scenario = network_configure_link.build(
            args.midbox_entity,
            args.middlebox_interface_wsc,
            'egress',
            'clear',
            args.bandwidth_wss_to_wsc,
            args.delay_wss_to_wsc,
            0,
            'random',
            args.loss_wss_to_wsc)
    #observer.launch_and_wait(scenario)
    scenario = network_configure_link.build(
            args.midbox_entity,
            args.middlebox_interface_wss,
            'egress',
            'clear',
            args.bandwidth_wsc_to_wss,
            args.delay_wsc_to_wss,
            0,
            'random',
            args.loss_wss_to_wsc)
    #observer.launch_and_wait(scenario)

    print("Tested executors are:")
    print(l_tested_executors)

if __name__ == '__main__':
    main()
