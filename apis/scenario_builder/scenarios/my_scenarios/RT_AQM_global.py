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
            start_RT_AQM_iperf = scenario.add_function(
                    'start_scenario_instance', wait_finished=wait_finished_list, wait_launched=wait_launched_list, wait_delay=int(args[7]) + 5)
            scenario_RT_AQM_iperf = RT_AQM_iperf.build(int(args[4]), post_processing_entity, [args[2], args[3]] + args[8:], scenario_id)
            start_RT_AQM_iperf.configure(scenario_RT_AQM_iperf)
            list_wait_finished.append(start_RT_AQM_iperf)
            map_scenarios[scenario_id] = start_RT_AQM_iperf

        if traffic == "dash":
            start_RT_AQM_DASH = scenario.add_function(
                    'start_scenario_instance', wait_finished=wait_finished_list, wait_launched=wait_launched_list, wait_delay=int(args[7]) + 5)
            scenario_RT_AQM_DASH = RT_AQM_DASH.build(int(args[4]), post_processing_entity, [args[2], args[3]] + args[8:], scenario_id)
            start_RT_AQM_DASH.configure(scenario_RT_AQM_DASH)
            list_wait_finished.append(start_RT_AQM_DASH)
            map_scenarios[scenario_id] = start_RT_AQM_DASH

        if traffic == "voip":
            start_RT_AQM_VOIP = scenario.add_function(
                    'start_scenario_instance', wait_finished=wait_finished_list, wait_launched=wait_launched_list, wait_delay=int(args[7]) + 5)
            scenario_RT_AQM_VOIP = RT_AQM_VOIP.build(int(args[4]), post_processing_entity, [args[2], args[3]] + args[8:], scenario_id)
            start_RT_AQM_VOIP.configure(scenario_RT_AQM_VOIP)
            list_wait_finished.append(start_RT_AQM_VOIP)
            map_scenarios[scenario_id] = start_RT_AQM_VOIP

    print(map_scenarios)

    # Add RT_AQM_initialize scenario
    start_RT_AQM_reset = scenario.add_function(
                'start_scenario_instance', wait_finished=list_wait_finished, wait_delay=5)
    scenario_RT_AQM_reset = RT_AQM_initialize.build(gateway_scheduler, interface_scheduler, "", "", reset_scheduler, reset_iptables, "RT_AQM_reset")
    start_RT_AQM_reset.configure(scenario_RT_AQM_reset)

    return scenario