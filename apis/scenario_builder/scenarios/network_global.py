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
from scenario_builder.scenarios import network_rate, network_delay, network_jitter, network_one_way_delay
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance



SCENARIO_DESCRIPTION="""This scenario is a wrapper of
        - network_delay,
        - network_one_way_delay
        - network_jitter
        - network_rate
        scenarios
"""
SCENARIO_NAME="""network_global"""

def build(client, server, ip_dst, port, command_port, duration, rate, num_flows, tos, mtu, bandwidth, post_processing_entity, scenario_name=SCENARIO_NAME):

    #Create top network_global scenario
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    # Add Delay metrology sub scenario
    start_network_delay = scenario.add_function(
                'start_scenario_instance')
    scenario_network_delay = network_delay.build(client, ip_dst, duration, 0, post_processing_entity)
    start_network_delay.configure(
                scenario_network_delay)

    # Add One Way Delay metrology sub scenario
    start_network_one_way_delay = scenario.add_function(
                'start_scenario_instance',wait_finished=[start_network_delay], wait_delay=2)
    scenario_network_one_way_delay = network_one_way_delay.build(client, server, ip_dst, post_processing_entity)
    start_network_one_way_delay.configure(
                scenario_network_one_way_delay)

    # Add Jitter metrology sub scenario
    start_network_jitter = scenario.add_function(
                'start_scenario_instance',wait_finished=[start_network_one_way_delay], wait_delay=2)
    scenario_network_jitter = network_jitter.build(client, server, ip_dst, port, duration, num_flows, tos, bandwidth, post_processing_entity)
    start_network_jitter.configure(
                scenario_network_jitter)

    # Add Rate metrology sub scenario
    start_network_rate = scenario.add_function(
        'start_scenario_instance',wait_finished=[start_network_jitter], wait_delay=2)
    scenario_network_rate = network_rate.build(client, server,ip_dst, port, command_port, duration, rate, num_flows, tos, mtu, post_processing_entity)
    start_network_rate.configure(
            scenario_network_rate)

    return scenario