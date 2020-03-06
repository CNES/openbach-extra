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
from scenario_builder.helpers.transport.tcp_conf_linux import tcp_conf_linux_variable_args_number
from scenario_builder.helpers.transport.ethtool import ethtool_disable_segmentation_offload
from scenario_builder.helpers.network.ip_route import ip_route
from inspect import signature


SCENARIO_DESCRIPTION = """This *transport_tcp_stack_conf* scenario allows to configure:
 - TCP congestion control and associated parameters,
 - route including TCP parameters like initial congestion and receive windows 
 - TCP segmentation offloading on a network interface.

If reset option is set, the sysctl and CUBIC parameters are reset to the value
they had at the installation of the job of tcp_conf_linux. Then the parameters
are updated only if a new value is set in the arguments. More information on
the wiki page of the job tcp_conf_linux.
"""
SCENARIO_NAME = 'transport_tcp_stack_conf'


def build(entity, tcp_params, tcp_subparams, interface=None, route=None, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    args = {'entity': entity, 'cc': tcp_params['congestion_control'], 'interface': interface}
    if route:
        args.update(route)

    for arg, value in args.items():
        if str(value).startswith('$'):
            scenario.add_argument(value[1:], '')

    tcp_conf_linux_variable_args_number(scenario, entity, tcp_params, tcp_subparams)

    if interface:
        ethtool_disable_segmentation_offload(scenario, entity, interface)

    if route and route.get('destination_ip') is not None:
        operation = route.pop('operation')
        ip_route(scenario, entity, operation, **route)
      
    return scenario
