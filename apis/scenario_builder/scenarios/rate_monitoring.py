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
from scenario_builder.helpers.metrology.rate_monitoring import tcp_rate_monitoring
from scenario_builder.helpers.metrology.rate_monitoring import udp_rate_monitoring
from scenario_builder.helpers.metrology.rate_monitoring import icmp_rate_monitoring
from scenario_builder.helpers.metrology.rate_monitoring import rate_monitoring
from inspect import signature


SCENARIO_DESCRIPTION="""This scenario allows to monitor a given flow, including:
     - bit rate
     - volume of sent data 
"""
SCENARIO_NAME="""rate_monitoring"""


def build(entity, interval, chain_name, source_ip=None, destination_ip=None, in_iface=None, out_iface=None, protocol=None, 
          sport=None, dport=None, scenario_name=SCENARIO_NAME):

    # Create scenario and add scenario arguments if needed
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    args = signature(build).parameters
    for arg in args:
        value = locals()[arg] 
        if str(value).startswith('$'):
           scenario.add_argument(value[1:], '')

    if protocol == 'tcp':
       tcp_rate_monitoring(scenario, entity, interval, chain_name, source_ip, destination_ip, in_iface, out_iface, sport, dport)
    elif protocol == 'udp':
       udp_rate_monitoring(scenario, entity, interval, chain_name, source_ip, destination_ip, in_iface, out_iface, sport, dport)
    elif protocol== 'icmp':
       icmp_rate_monitoring(scenario, entity, interval, chain_name, source_ip, destination_ip, in_iface, out_iface)
    else:
       rate_monitoring(scenario, entity, interval, chain_name, source_ip, destination_ip, in_iface)
       
       
    return scenario


