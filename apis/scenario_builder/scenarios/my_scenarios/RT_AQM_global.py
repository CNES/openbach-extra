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
from scenario_builder.scenarios.my_scenarios import RT_AQM_initialize, RT_AQM_iperf, RT_AQM_DASH, RT_AQM_VOIP
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance

from scenario_builder.helpers.transport.iperf3 import iperf3_rate_udp
from scenario_builder.helpers.service.dash import dash
from scenario_builder.helpers.service.voip import voip
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph



SCENARIO_DESCRIPTION="""This scenario is a wrapper of
        - RT_AQM_initialization
        - RT_AQM_iperf
        - RT_AQM_DASH
        - RT_AQM_web_transfer (TODO)
        - RT_AQM_voip
        - RT_AQM_reset
        scenarios
"""
SCENARIO_NAME="""RT_AQM_global"""

def extract_jobs_to_postprocess(scenario, traffic):
    if traffic == "iperf":
        for function_id, function in enumerate(scenario.openbach_functions):
            if isinstance(function, StartJobInstance):
                if function.job_name == 'iperf3':
                    if 'server' in function.start_job_instance['iperf3']:
                        port = function.start_job_instance['iperf3']['port']
                        address = function.start_job_instance['iperf3']['server']['bind']
                        yield (function_id, address, port)
    if traffic == "dash":
            for function_id, function in enumerate(scenario.openbach_functions):
                if isinstance(function, StartJobInstance):
                    print(function_id, function, function.start_job_instance)

            for function_id, function in enumerate(scenario.openbach_functions):
                if isinstance(function, StartJobInstance):
                    if function.job_name == 'dash player&server':
                        port = function.start_job_instance['dash player&server']['port']
                        #address = function.start_job_instance['dash player&server']['bind']
                        address = "Unknown address..." # TODO
                        yield (function_id, address, port)
    if traffic == "voip":
        for function_id, function in enumerate(scenario.openbach_functions):
            if isinstance(function, StartJobInstance):
                print(function_id, function, function.start_job_instance)

        for function_id, function in enumerate(scenario.openbach_functions):
            if isinstance(function, StartJobInstance):
                if function.job_name == 'voip_qoe_src':
                    port = function.start_job_instance['voip_qoe_src']['starting_port']
                    address = function.start_job_instance['voip_qoe_src']['dest_addr']
                    yield (function_id, address, port)

def generate_iptables(args_list):
    iptables = []

    for args in args_list:
        print(args)
        if args[1] == "iperf":
            address = args[8]
            port = args[9]
            iptables.append((address, "", port, "TCP", 16))
            iptables.append((address, "", port, "UDP", 16))
        if args[1] == "dash":
            address = args[9]
            port = args[10]
            iptables.append((address, port, "", "TCP", 24))
        if args[1] == "voip":
            address = args[9]
            port = args[10]
            iptables.append((address, "", port, "UDP", 0))

    return iptables


#1 iperf A1 A3 30 None None 0 192.168.2.9 5201 2M
#2 iperf A1 A3 30 None None 0 192.168.2.10 5201 2M
#3 dash A1 A3 30 None None 0 192.168.1.4 192.168.2.9 3001
#4 voip A1 A3 30 None None 0 192.168.1.4 192.168.2.9 8001 G.711.1


def build(gateway_scheduler, interface_scheduler, path_scheduler, duration, post_processing_entity, args_list, reset_scheduler, reset_iptables, scenario_name=SCENARIO_NAME):
    # Create top network_global scenario
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    list_wait_finished = []
    map_scenarios = {}

    # Add RT_AQM_initialize scenario
    start_RT_AQM_initialize = scenario.add_function('start_scenario_instance')
    scenario_RT_AQM_initialize = RT_AQM_initialize.build(gateway_scheduler, interface_scheduler, path_scheduler, generate_iptables(args_list), False, False)
    start_RT_AQM_initialize.configure(scenario_RT_AQM_initialize)

    # parsing arguments
    for args in args_list:
        print(args)
        traffic = args[1]
        scenario_id = args[0]
        wait_finished_list = [start_RT_AQM_initialize] + ([map_scenarios[i] for i in args[6].split('-')] if args[6] != "None" else [])
        wait_launched_list = ([map_scenarios[i] for i in args[5].split('-')] if args[5] != "None" else [])
        print(wait_finished_list,wait_launched_list)

        if traffic == "iperf":
            start_RT_AQM_iperf = iperf3_rate_udp(scenario, args[2], args[3], args[8], args[9], 1, int(args[4]), args[11], args[10],
                        wait_finished=wait_finished_list, wait_launched=wait_launched_list, wait_delay=int(args[7]) + 5)
            list_wait_finished += start_RT_AQM_iperf
            map_scenarios[scenario_id] = start_RT_AQM_iperf[0]

        if traffic == "dash":
            start_RT_AQM_DASH = dash(scenario, args[2], args[3], args[10], args[8], int(args[4]),
                        wait_finished=wait_finished_list, wait_launched=wait_launched_list, wait_delay=int(args[7]) + 5)
            list_wait_finished += start_RT_AQM_DASH
            map_scenarios[scenario_id] = start_RT_AQM_DASH[0]

        if traffic == "voip":
            start_RT_AQM_VOIP = voip(scenario, args[3], args[2], args[8], args[9], args[10], args[11], int(args[4]),
                        wait_finished=wait_finished_list, wait_launched=wait_launched_list, wait_delay=int(args[7]) + 5)
            list_wait_finished += start_RT_AQM_VOIP
            map_scenarios[scenario_id] = start_RT_AQM_VOIP[0]

    print(map_scenarios)

    # Add RT_AQM_initialize scenario
    start_RT_AQM_reset = scenario.add_function(
                'start_scenario_instance', wait_finished=list_wait_finished, wait_delay=5)
    scenario_RT_AQM_reset = RT_AQM_initialize.build(gateway_scheduler, interface_scheduler, "", "", reset_scheduler, reset_iptables, "RT_AQM_reset")
    start_RT_AQM_reset.configure(scenario_RT_AQM_reset)

    
    #Post processing partst
    if post_processing_entity is not None:
        post_processed = []
        legends = []
        for function_id, address, port in extract_jobs_to_postprocess(scenario, "iperf"):
            post_processed.append([function_id])
            legends.append([address + " " + str(port)])
            print(post_processed[-1],legends[-1])
            time_series_on_same_graph(scenario, post_processing_entity, [post_processed[-1]], [['throughput']], [['Rate (b/s)']], [['Rate time series']], [legends[-1]], [start_RT_AQM_reset], None, 2)

        time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['throughput']], [['Rate (b/s)']], [['Rate time series']], legends, [start_RT_AQM_reset], None, 2)

        post_processed = []
        legends = []
        for function_id, address, port in extract_jobs_to_postprocess(scenario, "dash"):
            post_processed.append([function_id])
            legends.append([address + " " + str(port)])
            print(post_processed[-1],legends[-1])
            time_series_on_same_graph(scenario, post_processing_entity, [post_processed[-1]], [['bitrate']], [['Rate (b/s)']], [['Rate time series']], [legends[-1]], [start_RT_AQM_reset], None, 2)

        time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['bitrate']], [['Rate (b/s)']], [['Rate time series']], legends, [start_RT_AQM_reset], None, 2)

        post_processed = []
        legends = []
        for function_id, address, port in extract_jobs_to_postprocess(scenario, "voip"):
            post_processed.append([function_id])
            legends.append([address + " " + str(port)])
            print(post_processed[-1],legends[-1])
            time_series_on_same_graph(scenario, post_processing_entity, [post_processed[-1]], [['instant_mos']], [['MOS']], [['Rate time series']], [legends[-1]], [start_RT_AQM_reset], None, 2)

        time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['instant_mos']], [['MOS']], [['Rate time series']], legends, [start_RT_AQM_reset], None, 2)

    return scenario