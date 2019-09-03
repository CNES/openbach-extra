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


SCENARIO_DESCRIPTION="""Reset scheduler and iptables if requested"""
SCENARIO_NAME="""RT_AQM_reset"""

def reset_config(scenario, gateway, interface, reset_scheduler, reset_iptables):

    if reset_scheduler:
        scheduler_del = scenario.add_function('start_job_instance')
        scheduler_del.configure(
                'ip_scheduler', gateway, offset=0,
                 interface_name=interface,remove={})

    if reset_iptables:
        iptables_del = scenario.add_function('start_job_instance')
        iptables_del.configure(
                'iptables', gateway, offset=0,
                rule="-t mangle -F")

    return scenario


def build(gateway, interface, reset_scheduler, reset_iptables, scenario_name=SCENARIO_NAME):
    print("loading:",scenario_name)

    # Create scenario
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    reset_config(scenario, gateway, interface, reset_scheduler, reset_iptables)

    return scenario