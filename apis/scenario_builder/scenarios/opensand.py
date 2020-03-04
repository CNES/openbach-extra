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
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance
from scenario_builder.helpers import push_file
from scenario_builder.scenarios import opensand_configure, opensand_run

SCENARIO_DESCRIPTION="""This is reference OpenSAND scenario"""
SCENARIO_NAME="""opensand"""

def build(gw, sat_entity, sat_interface, sat_ip, duration, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    start_scenario_configure = scenario.add_function('start_scenario_instance')

    #Configure
    scenario_configure = opensand_configure.build(gw, sat_entity, sat_interface, sat_ip)
    start_scenario_configure.configure(scenario_configure)

    #Run and stop
    start_scenario_run = scenario.add_function('start_scenario_instance', wait_finished = [start_scenario_configure])
    scenario_run = opensand_run.build(gw, sat_entity, sat_ip)
    start_scenario_run.configure(scenario_run)
    
    stopper = scenario.add_function('stop_scenario_instance', wait_launched = [start_scenario_run], wait_delay = duration)
    stopper.configure(start_scenario_run)    

    #Opensand!
    #push_file(scenario, entity, '/opt/openbach/agent/files/testing/bite.txt', '/opt/openbach/agent/bite.txt')
    #push_file(scenario, entity, '/opt/openbach/agent/files/testing/toto.txt', '/opt/openbach/agent/toto.txt')
    return scenario
