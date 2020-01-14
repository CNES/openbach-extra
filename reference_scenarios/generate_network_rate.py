#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2019 CNES
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

"""This scenario launches the *network_rate* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_rate


def main(scenario_name='generate_network_rate', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', required=True,
            help='name of the entity for the client iperf3/nuttcp')
    observer.add_scenario_argument(
            '--server', '--server-entity', required=True,
            help='name of the entity for the server iperf3/nuttcp')
    observer.add_scenario_argument(
            '--ip_dst', required=True, help='The server IP address')
    observer.add_scenario_argument(
            '--port', default=7000,  help='The iperf3/nuttcp server port for data')
    observer.add_scenario_argument(
            '--duration', default=30, help='duration of iperf3/nuttcp tests')
    observer.add_scenario_argument(
            '--command_port', default=7001, help='The port of nuttcp server for signalling')
    observer.add_scenario_argument(
            '--rate', help='Set a higher rate (in kb/s) than what you estimate between server and client '
            'for the UDP test (add m/g to set M/G b/s)', required=True)
    observer.add_scenario_argument(
            '--num_flows', default=1, help='Number of iperf3 flows generated (default : 1)')
    observer.add_scenario_argument(
            '--tos', default=0, help='Type of Service of the trafic (default : 0)')
    observer.add_scenario_argument(
            '--mtu', default=1000-40, help='MTU size (default : 1000-40)')
    observer.add_scenario_argument(
            '--entity_pp', help='The entity where the post-processing will be '
            'performed (histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, scenario_name)

    scenario = network_rate.build(
            args.client,
            args.server,
            args.ip_dst,
            args.port,
            args.command_port,
            args.duration,
            args.rate,
            args.num_flows,
            args.tos,
            args.mtu,
            args.entity_pp)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
