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
from scenario_builder.scenarios import transport_tcp_stack_conf, service_traffic_mix 
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance
import itertools


SCENARIO_DESCRIPTION="""This scenario allows to configure the tcp stack and launch a service traffic mix scenario
"""
SCENARIO_NAME="""Traffic_mix_performances"""

def build(server, interface, cc, init_cwnd, extra_args_traffic, post_processing_entity, scenario_name=SCENARIO_NAME):
    ccs = ('cubic','reno')
    initcwnds = ('10', '30')
    tcp_configurations = list(itertools.product(ccs, initcwnds))
    #Create top scenario
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    wait_finished = []
    for initcwnd, cc in tcp_configurations:
        # Launch transport configuration tcp stack scenario
        start_conf_tcp = scenario.add_function(
                    'start_scenario_instance', wait_finished=wait_finished, wait_delay=5)
        scenario_tcp_conf = transport_tcp_stack_conf.build(server, interface, cc, initcwnd)
        start_conf_tcp.configure(
                    scenario_tcp_conf)
        wait_finished.append(start_conf_tcp) 
        # Launch traffix_mix scenario
        start_traffic_mix = scenario.add_function('start_scenario_instance',
                        wait_finished=wait_finished, wait_delay=5)
        scenario_traffic_mix = service_traffic_mix.build(post_processing_entity, extra_args_traffic)
        start_traffic_mix.configure(scenario_traffic_mix)
        wait_finished.append(start_traffic_mix)

    return scenario
