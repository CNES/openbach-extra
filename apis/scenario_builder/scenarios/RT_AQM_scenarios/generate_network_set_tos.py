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


SCENARIO_DESCRIPTION="""Initialize or remove iptables to set ToS field"""
SCENARIO_NAME="""generate_network_set_tos"""

def reset(scenario, gateway):
    iptables = scenario.add_function('start_job_instance')
    iptables.configure(
                'iptables', gateway, offset=0,
                rule="-t mangle -F")

    return iptables

def initialize(scenario, gateway, iptables):

    rst = reset(scenario, gateway)

    prev_job = [rst]
    for address,src_port,dst_port,protocol,tos in iptables:
        iptable = scenario.add_function('start_job_instance',
            wait_finished=prev_job, wait_launched=None, wait_delay=1)
        if src_port:
            iptable.configure(
                    'iptables', gateway, offset=0,
                    rule="-t mangle -A PREROUTING -d " + address + " -p " + protocol + " --sport " + str(src_port) + " -j TOS --set-tos " + str(tos))
        if dst_port:
            iptable.configure(
                    'iptables', gateway, offset=0,
                    rule="-t mangle -A PREROUTING -d " + address + " -p " + protocol + " --dport " + str(dst_port) + " -j TOS --set-tos " + str(tos))
        prev_job = [iptable]

    return scenario


def build(gateway, iptables, action, scenario_name=SCENARIO_NAME):
    print("loading:",scenario_name + "_" + action)

    # Create scenario
    scenario = Scenario(scenario_name + "_" + action, SCENARIO_DESCRIPTION)

    if action == "init":
        initialize(scenario, gateway, iptables)
    if action == "reset":
        reset(scenario, gateway)

    return scenario