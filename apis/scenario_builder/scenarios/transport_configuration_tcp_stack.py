#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
from scenario_builder.helpers.transport.tcp_conf_linux import tcp_conf_linux_repetitive_tests
from scenario_builder.helpers.transport.ethtool import ethtool_disable_segmentation_offload
from scenario_builder.helpers.network.ip_route import ip_route
from inspect import signature


SCENARIO_DESCRIPTION="""This *transport_configuration_tcp_stack* scenario allows to configure:
     - TCP congestion control, 
     - route including TCP parameters like initial congestion and receive windows 
     - TCP segmentation offloading on a network interface.
"""
SCENARIO_NAME="""transport_configuration_tcp_stack"""


def build(entity, cc=None, interface=None, route=None, scenario_name=SCENARIO_NAME):
    # Create scenario and add scenario arguments if needed
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    args = {'entity': entity, 'cc':cc, 'interface':interface}
    args.update(route if route else {})
    for arg, value in args.items():
        if str(value).startswith('$'):
           scenario.add_argument(value[1:], '')
    if cc:
       tcp_conf_linux_repetitive_tests(scenario, entity, cc)
    if interface:
       ethtool_disable_segmentation_offload(scenario, entity, interface)
    if route:
       ip_route(scenario, entity, 'change', **route)
      
    return scenario


