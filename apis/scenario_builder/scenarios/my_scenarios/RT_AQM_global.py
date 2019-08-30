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

def generate_iptables(args):
    iptables = []
    # TODO remove next line
    # return iptables
    for traffic,params in args:
        if traffic == "iperf":
            address = params[2]
            port = params[3]
            iptables.append((address,"",port,"TCP",16))
            iptables.append((address,"",port,"UDP",16))
        if traffic == "dash":
            address = params[2]
            port = params[3]
            iptables.append((address,port,"","TCP",24))
        if traffic == "voip":
            address = params[3]
            port = params[4]
            iptables.append((address,"",port,"UDP",0))
    return iptables

def build(gateway_scheduler, interface_scheduler, path_scheduler, duration, post_processing_entity, args, reset_scheduler, reset_iptables, scenario_name=SCENARIO_NAME):
    # Create top network_global scenario
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    list_wait_finished = []

    # Add RT_AQM_initialize scenario
    start_RT_AQM_initialize = scenario.add_function(
                'start_scenario_instance')
    scenario_RT_AQM_initialize = RT_AQM_initialize.build(gateway_scheduler, interface_scheduler, path_scheduler, generate_iptables(args), False, False)
    start_RT_AQM_initialize.configure(scenario_RT_AQM_initialize)

    # Add RT_AQM_iperf scenario
    args_iperf = [line[1] for line in args if line[0] == "iperf"]
    scenario_id = 1
    for arg_iperf in args_iperf:
        start_RT_AQM_iperf = scenario.add_function(
                    'start_scenario_instance', wait_finished=[start_RT_AQM_initialize], wait_delay=2)
        scenario_RT_AQM_iperf = RT_AQM_iperf.build(duration, post_processing_entity, arg_iperf, scenario_id)
        start_RT_AQM_iperf.configure(scenario_RT_AQM_iperf)
        list_wait_finished.append(start_RT_AQM_iperf)
        scenario_id += 1

    # Add RT_AQM_DASH scenario
    args_dash = [line[1] for line in args if line[0] == "dash"]
    scenario_id = 1
    for arg_dash in args_dash:
        start_RT_AQM_DASH = scenario.add_function(
                   'start_scenario_instance', wait_finished=[start_RT_AQM_initialize], wait_delay=2)
        scenario_RT_AQM_DASH = RT_AQM_DASH.build(duration, post_processing_entity, arg_dash, scenario_id)
        start_RT_AQM_DASH.configure(scenario_RT_AQM_DASH)
        list_wait_finished.append(start_RT_AQM_DASH)
        scenario_id += 1

    # Add RT_AQM_VoIP scenario
    args_voip = [line[1] for line in args if line[0] == "voip"]
    scenario_id = 1
    for arg_voip in args_voip:
        start_RT_AQM_VOIP = scenario.add_function(
                   'start_scenario_instance', wait_finished=[start_RT_AQM_initialize], wait_delay=2)
        scenario_RT_AQM_VOIP = RT_AQM_VOIP.build(duration, post_processing_entity, arg_voip, scenario_id)
        start_RT_AQM_VOIP.configure(scenario_RT_AQM_VOIP)
        list_wait_finished.append(start_RT_AQM_VOIP)
        scenario_id += 1

    # Add RT_AQM_initialize scenario
    start_RT_AQM_reset = scenario.add_function(
                'start_scenario_instance', wait_finished=list_wait_finished, wait_delay=5)
    scenario_RT_AQM_reset = RT_AQM_initialize.build(gateway_scheduler, interface_scheduler, "", "", reset_scheduler, reset_iptables, "RT_AQM_reset")
    start_RT_AQM_reset.configure(scenario_RT_AQM_reset)

    return scenario