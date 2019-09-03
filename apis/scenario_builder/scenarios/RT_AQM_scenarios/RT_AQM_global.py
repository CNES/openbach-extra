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
from scenario_builder.scenarios.RT_AQM_scenarios import RT_AQM_initialize, RT_AQM_reset, RT_AQM_traffic_generation


SCENARIO_DESCRIPTION="""This scenario launches the following in-order:
        - RT_AQM_initialization
        - RT_AQM_traffic_generation
        - RT_AQM_reset
"""
SCENARIO_NAME="""RT_AQM_global"""

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
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    list_wait_finished = []
    map_scenarios = {}

    # Add RT_AQM_initialize scenario
    start_RT_AQM_initialize = scenario.add_function('start_scenario_instance')
    scenario_RT_AQM_initialize = RT_AQM_initialize.build(gateway_scheduler, interface_scheduler, path_scheduler, generate_iptables(args_list))
    start_RT_AQM_initialize.configure(scenario_RT_AQM_initialize)

    # Launching traffic
    start_RT_AQM_traffic_generation = scenario.add_function('start_scenario_instance', wait_finished=[start_RT_AQM_initialize], wait_delay=5)
    scenario_RT_AQM_traffic_generation = RT_AQM_traffic_generation.build(post_processing_entity, args_list)
    start_RT_AQM_traffic_generation.configure(scenario_RT_AQM_traffic_generation)

    # Add RT_AQM_reset scenario
    start_RT_AQM_reset = scenario.add_function(
                'start_scenario_instance', wait_finished=[start_RT_AQM_traffic_generation], wait_delay=5)
    scenario_RT_AQM_reset = RT_AQM_reset.build(gateway_scheduler, interface_scheduler, reset_scheduler, reset_iptables)
    start_RT_AQM_reset.configure(scenario_RT_AQM_reset)

    print("All scenarios loaded, launching simulation")

    return scenario