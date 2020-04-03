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


SCENARIO_DESCRIPTION = """This scenario allows to:
 - Add/Remove a scheduler on ip layer on the chosen interface.
   This scheduler works with three levels of scheduling: per trunk, per destination, and per Class of Service.
"""


def add_qos(entity, interface_name, path, scenario_name='add_network_qos'):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    function = scenario.add_function('start_job_instance')
    function.configure('ip_scheduler', entity, interface_name=interface_name, add={"file_path":path})
    return scenario


def remove_qos(entity, interface_name, scenario_name='remove_network_qos'):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    function = scenario.add_function('start_job_instance')
    function.configure('ip_scheduler', entity, interface_name=interface_name, remove={})
    return scenario


def build(entity, interface_name, action, path, scenario_name=None):

    scenario = add_qos(entity, interface_name, path) if action == "add" else remove_qos(entity, interface_name)

    if scenario_name is not None:
        scenario.name = scenario_name
 
    return scenario


