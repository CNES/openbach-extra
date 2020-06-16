#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2020 CNES
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

"""This executor builds or launches the *network_global* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
composed of all basic network qos basics : network_delay, network_jitter,
network_rate, network_one_way_delay.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_global

def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the entity for the server of the global tests')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the entity for the client of global tests')
    observer.add_scenario_argument(
            '--server-ip', required=True,
            help='server ip address and target of the global network test')
    observer.add_scenario_argument(
            '--client-ip', required=True,
            help='IP address of source of pings and packets')
    observer.add_scenario_argument(
            '--server-port', default=7001,
            help='The iperf3/nuttcp server port for data')
    observer.add_scenario_argument(
            '--command-port', default=7000,
            help='The port of nuttcp server for signalling')
    observer.add_scenario_argument(
            '--duration', default=30,
            help='duration of each delay, rate,   scenario (s)')
    observer.add_scenario_argument(
            '--rate-limit', required=True,
            help='Set a higher rate (in kb/s) '
            'than what you estimate between server and client for the '
            'UDP test (add m/g to set M/G b/s)')
    observer.add_scenario_argument(
            '--num-flows', default=1,
            help='Number of iperf3 flows generated (default : 1)')
    observer.add_scenario_argument(
            '--bandwidth', default='1M',
            help='the bandwidth (bits/s) of iperf3 test')
    observer.add_scenario_argument(
            '--tos', default=0,
            help='Type of Service of the trafic (default : 0)')
    observer.add_scenario_argument(
            '--mtu', default=1400,
            help='MTU size (default : 1400)')
    observer.add_scenario_argument(
            '--count', default=100,
            help='The number of owamp packets to send')
    observer.add_scenario_argument(
            '--interval', default='0.1e',
            help='The mean average time between owamp packets (specify seconds and distribution type)'
            'If e: random exponential distribution. If f: constant distribution')
    observer.add_scenario_argument(
            '--post-processing-entity',
            help='The entity where the post-processing will be '
            'performed (histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, network_global.SCENARIO_NAME)

    scenario = network_global.build(
                      args.server_entity,
                      args.client_entity,
                      args.server_ip,
                      args.client_ip,
                      args.server_port,
                      args.command_port,
                      args.duration,
                      args.rate_limit,
                      args.num_flows,
                      args.bandwidth,
                      args.tos,
                      args.mtu,
                      args.count,
                      args.interval,
                      args.post_processing_entity,
                      scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()