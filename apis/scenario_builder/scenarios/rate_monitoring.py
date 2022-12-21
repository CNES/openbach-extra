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
from scenario_builder.openbach_functions import StartJobInstance
from scenario_builder.helpers.transport.rate_monitoring import rate_monitoring


SCENARIO_NAME = 'rate_monitoring'
SCENARIO_DESCRIPTION = """This rate_monitoring scenario allows to
    measures the rate (b/s) of a flow. It uses an //iptable// 
    entry to measure the number of packets and the size of data 
    of a chain.
"""


def build(sampling_interval, entity, chain_name, source_ip=None,
        destination_ip=None, in_interface=None, out_interface=None,
        scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    rate_monitoring(scenario, entity, sampling_interval, chain_name, source_ip,
        destination_ip, in_interface, out_interface)

    return scenario
