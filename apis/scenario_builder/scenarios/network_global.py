#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016−2020 CNES
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

SCENARIO_NAME = 'network_global'
SCENARIO_DESCRIPTION = """This scenario is a wrapper for the following scenarios:
 - network_delay,
 - network_one_way_delay
 - network_jitter
 - network_rate
 NB : client = traffic sender and server = traffic receiver
It is a general network QoS metrics scenario.
"""


def build(
        server_entity, client_entity, server_ip, client_ip, server_port, command_port,
        rate, num_flows, bandwidth, tos, mtu, duration,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):

    #Create top network_global scenario
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    # Add Delay metrology sub scenario
    scenario_network_delay = network_delay.build(server_entity, client_entity, server_ip, client_ip, False, duration, post_processing_entity)
    start_network_delay = scenario.add_function('start_scenario_instance')
    start_network_delay.configure(scenario_network_delay)

    # Add One Way Delay metrology sub scenario
    scenario_network_one_way_delay = network_one_way_delay.build(
            server_entity, client_entity, server_ip, client_ip, post_processing_entity)
    start_network_one_way_delay = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_network_delay],
            wait_delay=2)
    start_network_one_way_delay.configure(scenario_network_one_way_delay)

    # Add Jitter metrology sub scenario
    scenario_network_jitter = network_jitter.build(
            server_entity, client_entity, server_ip, server_port,
            num_flows, bandwidth, tos, duration, post_processing_entity)
    start_network_jitter = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_network_one_way_delay],
            wait_delay=2)
    start_network_jitter.configure(scenario_network_jitter)

    # Add Rate metrology sub scenario
    scenario_network_rate = network_rate.build(
            server_entity, client_entity, server_ip, client_ip, server_port, command_port,
            rate, num_flows, tos, mtu, duration, post_processing_entity)
    start_network_rate = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_network_jitter],
            wait_delay=2)
    start_network_rate.configure(scenario_network_rate)

    return scenario
