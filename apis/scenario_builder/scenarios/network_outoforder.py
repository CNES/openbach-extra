#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2023 CNES
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
from scenario_builder.helpers.network.outoforder_detect import outoforder_detect, outoforder_find_server
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance


SCENARIO_NAME = 'network_outoforder'
SCENARIO_DESCRIPTION = """This network_outoforder scenario allows to:
 - Detect packets deordering and packets duplication between a Client and a Server
 - NB : The analysis is performed in one direction only (from Client to Server).
"""

def outoforder(
        server_entity, client_entity, server_ip, duration, transmitted_packets,
        server_port, signal_port, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('duration', duration)
    scenario.add_constant('server_port', server_port)
    scenario.add_constant('signal_port', signal_port)

    wait = outoforder_detect(
            scenario, server_entity, client_entity, '$server_ip', '$duration', transmitted_packets, '$server_port', '$signal_port')

    return scenario


def build(
        server_entity, client_entity, server_ip, duration,
        transmitted_packets, server_port, signal_port,
        scenario_name=SCENARIO_NAME):
    scenario = outoforder(
            server_entity, client_entity, server_ip, duration,
            transmitted_packets, server_port, signal_port, scenario_name)
    return scenario

