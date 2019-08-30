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



SCENARIO_DESCRIPTION="""Initializes scheduler and iptables"""
SCENARIO_NAME="""RT_AQM_initialize"""

def initialize_core(scenario, gateway, interface, path, iptables):

    scheduler = scenario.add_function('start_job_instance')
    scheduler.configure(
            'ip_scheduler', gateway, offset=0,
             interface_name=interface,
             add={'file_path': path})

    iptables_del = scenario.add_function('start_job_instance')
    iptables_del.configure(
            'iptables', gateway, offset=0,
            rule="-t mangle -F")

    for address,src_port,dst_port,protocol,tos in iptables:
        iptable = scenario.add_function(
            'start_job_instance',
            wait_finished=[iptables_del],
            wait_launched=None,
            wait_delay=2)
        if src_port:
            iptable.configure(
                    'iptables', gateway, offset=0,
                    rule="-t mangle -A PREROUTING -d " + address + " -p " + protocol + " --sport " + str(src_port) + " -j TOS --set-tos " + str(tos))
        if dst_port:
            iptable.configure(
                    'iptables', gateway, offset=0,
                    rule="-t mangle -A PREROUTING -d " + address + " -p " + protocol + " --dport " + str(dst_port) + " -j TOS --set-tos " + str(tos))

    return scenario

def build(gateway, interface, path, iptables, scenario_name=SCENARIO_NAME):

    print(scenario_name)

    # Create scenario and subscenario core
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    initialize_core(scenario, gateway, interface, path, iptables)

    return scenario