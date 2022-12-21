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
from scenario_builder.helpers.transport.pep import pep
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance

SCENARIO_NAME = 'transport_pep'
SCENARIO_DESCRIPTION = """This transport_pep scenario launches 
PEPSal, and sets up the routes and iptables configurations necessary 
to perform TCP splitting."""


def launch_pep(
        entity, address, port, fastopen, maxconns, gcc_interval, log_file,
        pending_lifetime, stop, redirect_ifaces, redirect_src_ip, redirect_dst_ip,
        mark, table_num, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    pep(scenario, entity, address, port, fastopen, maxconns, gcc_interval, log_file,
            pending_lifetime, stop, redirect_ifaces, redirect_src_ip, redirect_dst_ip, mark, table_num)

    return scenario


def build(entity, address=None, port=None, fastopen=None, maxconns=None,
        gcc_interval=None, log_file=None, pending_lifetime=None, stop=None,
        redirect_ifaces=None, redirect_src_ip=None, redirect_dst_ip=None, mark=None,
        table_num=None, duration=None, scenario_name=SCENARIO_NAME):

    scenario = launch_pep(entity, address, port, fastopen, maxconns, gcc_interval, log_file, pending_lifetime,
            stop, redirect_ifaces, redirect_src_ip, redirect_dst_ip, mark, table_num, scenario_name)


    if duration:
        jobs = [f for f in scenario.openbach_functions if isinstance(f, StartJobInstance)]
        scenario.add_function('stop_job_instance', wait_launched=jobs, wait_delay=duration).configure(*jobs)


    return scenario


