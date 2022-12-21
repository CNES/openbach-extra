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

"""This executor builds or launches the *network_outoforder* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
It checks if the the link between a client and a server introduces packets deordering and/or packets duplication.
The analysis is performed in the Client --> Server direction.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_outoforder

def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the entity for the server')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the entity for the client ')
    observer.add_scenario_argument(
            '--server-ip', required=True, help='The server IP address')
    observer.add_scenario_argument(
            '--server-port', type=int, default=61234,
            help='The server port for data')
    observer.add_scenario_argument(
            '--signal-port', type=int, default=61235,
            help='Signalisation port to manage connection between client and server')
    observer.add_scenario_argument(
            '--duration', type=float, default=5,
            help='The duration of the transmission in seconds. Set 0 to infinite test')
    observer.add_scenario_argument(
            '--transmitted-packets', type=str,
            help='The number of packets to transmit. It has same priority as duration parameter. You can '
            'use [K/M/G]: set 100K to send 100.000 packets.')

    args = observer.parse(argv, network_outoforder.SCENARIO_NAME)

    scenario = network_outoforder.build(
            args.server_entity,
            args.client_entity,
            args.server_ip,
            args.duration,
            args.transmitted_packets,
            args.server_port,
            args.signal_port,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
