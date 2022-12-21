#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2023 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

"""This executor builds or launches the *network_mtu* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
It launches network tests to discover the path MTU between 2 distant machines.
The analysis is performed in 1 single direction : from the client to the server.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_mtu


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='Name of the entity which launches the test (source of the tested path)')
    observer.add_scenario_argument(
            '--server-ip', required=True,
            help='Destination ip address or domain (destination of the tested path)')

    args = observer.parse(argv, network_mtu.SCENARIO_NAME)

    scenario = network_mtu.build(
                      args.client_entity,
                      args.server_ip,
                      scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()

