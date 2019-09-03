#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016−2019 CNES
#
#
#   This file is part of the OpenBACH testbed.
#
#
#   OpenBACH is a free software : you can redistribute it and/or modify it under
#   the terms of the GNU General Public License as published by the Free Software
#   Foundation, either version 3 of the License, or (at your option) any later
#   version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
#   details.
#
#   You should have received a copy of the GNU General Public License along with
#   this program. If not, see http://www.gnu.org/licenses/.


from scenario_builder import Scenario
from scenario_builder.openbach_functions import StartJobInstance
from scenario_builder.helpers.service.apache2 import apache2
from scenario_builder.scenarios.RT_AQM_scenarios import generate_network_iptables, generate_network_scheduler
from scenario_builder.scenarios.RT_AQM_scenarios import generate_service_data_transfer, generate_service_video_dash, generate_service_web_browsing, generate_service_voip
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph


SCENARIO_DESCRIPTION="""This scenario launches the following in-order:
        - RT_AQM_initialization
        - All the traffics as defined in the configuration file
        - RT_AQM_reset
        - Post processing
"""
SCENARIO_NAME="""generate_service_traffic_mix"""

def extract_jobs_to_postprocess(scenarios, traffic):
    for scenario, start_scenario in scenarios:
        for function_id, function in enumerate(scenario.openbach_functions):
            if isinstance(function, StartJobInstance):
                if traffic == "iperf" and function.job_name == 'iperf3':
                    if 'server' in function.start_job_instance['iperf3']:
                        port = function.start_job_instance['iperf3']['port']
                        address = function.start_job_instance['iperf3']['server']['bind']
                        yield (start_scenario, function_id, address + " " + str(port))
                if traffic == "dash" and function.job_name == 'dash player&server':
                    port = function.start_job_instance['dash player&server']['port']
                    #address = function.start_job_instance['dash player&server']['bind']
                    address = "Unknown address..." # TODO
                    yield (start_scenario, function_id, address + " " + str(port))
                if traffic == "voip" and function.job_name == 'voip_qoe_src':
                    port = function.start_job_instance['voip_qoe_src']['starting_port']
                    address = function.start_job_instance['voip_qoe_src']['dest_addr']
                    yield (start_scenario, function_id, address + " " + str(port))
                if traffic == "web" and function.job_name == 'web_browsing_qoe':
                    dst = function.start_job_instance['entity_name']
                    port = "Unknown port..." # TODO
                    yield (start_scenario, function_id, dst + " " + str(port))

def generate_iptables(args_list):
    iptables = []

    for args in args_list:
        if args[1] == "iperf":
            address = args[8]
            port = args[9]
            iptables.append((address, "", port, "TCP", 16))
            iptables.append((address, "", port, "UDP", 16))
        if args[1] == "dash":
            address = args[9]
            port = args[10]
            iptables.append((address, port, "", "TCP", 24))
        if args[1] == "web":
            address = args[9]
            iptables.append((address, 8082, "", "TCP", 8))
        if args[1] == "voip":
            address = args[9]
            port = args[10]
            iptables.append((address, "", port, "UDP", 0))

    return iptables


def build(gateway_scheduler, interface_scheduler, path_scheduler, post_processing_entity, args_list, reset_scheduler, reset_iptables, scenario_name=SCENARIO_NAME):
    # Create top network_global scenario
    scenario_mix = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    list_wait_finished = []
    list_scenarios = []
    apache_servers = {}
    map_scenarios = {}

    # Add ip_scheduler
    start_ip_scheduler_init = scenario_mix.add_function('start_scenario_instance')
    scenario_ip_scheduler_init = generate_network_scheduler.build(gateway_scheduler, interface_scheduler, path_scheduler, "init")
    start_ip_scheduler_init.configure(scenario_ip_scheduler_init)

    # Add iptables
    start_iptables_init = scenario_mix.add_function('start_scenario_instance')
    scenario_iptables_init = generate_network_iptables.build(gateway_scheduler, generate_iptables(args_list), "init")
    start_iptables_init.configure(scenario_iptables_init)

    #launching Apache2 servers first
    start_RT_AQM_WEB_servers = []
    for args in args_list:
        if args[1] == "web" and args[2] not in apache_servers:
            start_RT_AQM_WEB_server = apache2(scenario_mix, args[2], "start",
                    wait_finished=[start_ip_scheduler_init, start_iptables_init], wait_launched=None, wait_delay=5)[0]
            apache_servers[args[2]] = start_RT_AQM_WEB_server
            start_RT_AQM_WEB_servers.append(start_RT_AQM_WEB_server)

    # Creating and launching traffic scenarios
    for args in args_list:
        traffic = args[1]
        scenario_id = args[0]
        if args[5] == "None" and args[6] == "None":
            wait_finished_list = []
            wait_launched_list = start_RT_AQM_WEB_servers if start_RT_AQM_WEB_servers else []
            offset_delay = 5
        else:
            wait_finished_list = [map_scenarios[i] for i in args[6].split('-')] if args[6] != "None" else []
            wait_launched_list = [map_scenarios[i] for i in args[5].split('-')] if args[5] != "None" else []
            offset_delay = 0

        start_scenario = scenario_mix.add_function('start_scenario_instance',
                    wait_finished=wait_finished_list, wait_launched=wait_launched_list, wait_delay=int(args[7]) + offset_delay)
        if traffic == "iperf":
            scenario = generate_service_data_transfer.build(post_processing_entity, args)
        if traffic == "dash":
            scenario = generate_service_video_dash.build(post_processing_entity, args)
        if traffic == "web":
            scenario = generate_service_web_browsing.build(post_processing_entity, args)
        if traffic == "voip":
            scenario = generate_service_voip.build(post_processing_entity, args)

        start_scenario.configure(scenario)
        list_wait_finished += [start_scenario]
        map_scenarios[scenario_id] = start_scenario
        list_scenarios.append((scenario, start_scenario))
        
    # stopping all Apache2 servers
    for server_entity,scenario_server in apache_servers.items():
        stopper = scenario_mix.add_function(
                'stop_job_instance',
                wait_finished=list_wait_finished, wait_delay=5)
        stopper.configure(scenario_server)
        apache2(scenario_mix, server_entity, "stop",
                wait_finished=list_wait_finished, wait_delay=5)

    # Removes ip_scheduler
    if reset_scheduler:
        start_ip_scheduler_init = scenario_mix.add_function('start_scenario_instance',
                wait_finished=list_wait_finished, wait_delay=5)
        scenario_ip_scheduler_init = generate_network_scheduler.build(gateway_scheduler, interface_scheduler, path_scheduler, "reset")
        start_ip_scheduler_init.configure(scenario_ip_scheduler_init)

    # Removes iptables
    if reset_iptables:
        start_iptables_init = scenario_mix.add_function('start_scenario_instance',
                wait_finished=list_wait_finished, wait_delay=5)
        scenario_iptables_init = generate_network_iptables.build(gateway_scheduler, generate_iptables(args_list), "reset")
        start_iptables_init.configure(scenario_iptables_init)

    # Post processing data
    if post_processing_entity is not None:
        print("Loading:", "post processing")
        for traffic, name, y_axis in [("iperf", "throughput", "Rate (b/s)"),
                                        ("dash", "bitrate", "Rate (b/s)"),
                                        ("web", "page_load_time", "PLT (ms)"),
                                        ("voip", "instant_mos", "MOS")]:
            post_processed = []
            legends = []
            for scenario_id, function_id, legend in extract_jobs_to_postprocess(list_scenarios, traffic):
                post_processed.append([scenario_id, function_id])
                legends.append([legend])
            if post_processed:
                time_series_on_same_graph(scenario_mix, post_processing_entity, post_processed, [[name]], [[y_axis]], [['Rate time series']], legends, list_wait_finished, None, 2)
                cdf_on_same_graph(scenario_mix, post_processing_entity, post_processed, 100, [[name]], [[y_axis]], [['Rate CDF']], legends, list_wait_finished, None, 2)

    print("All scenarios loaded, launching simulation")

    return scenario_mix