#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from scenario_builder.helpers.network.mtu_discovery import mtu_discovery
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance

SCENARIO_NAME = 'network_mtu'
SCENARIO_DESCRIPTION = """This network_mtu scenario allows to
discover the path MTU between 2 distant machines.
"""


def mtu(client_entity, server_ip, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    mtu_discovery(scenario, client_entity, server_ip)
    return scenario


def build(client_entity, server_ip, scenario_name=SCENARIO_NAME):
    scenario = mtu(client_entity, server_ip, scenario_name)
    return scenario

