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

"""This script launches the *network_jitter* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_jitter


def main(scenario_name='executor_network_jitter', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the entity for the server of the owamp RTT test')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the entity for the client of the RTT tests')
    observer.add_scenario_argument(
            '--server-ip', required=True, help='server ip address and target of the pings')
    observer.add_scenario_argument(
            '--server-port', default=7000, help='the iperf3 server port for data')
    observer.add_scenario_argument(
            '--duration', default=10,
            help='the duration of iperf3 test')
    observer.add_scenario_argument(
            '--num-flows', default=1,
            help='the number of flows to launch with iperf3')
    observer.add_scenario_argument(
            '--tos', default=0,
            help='the ToS of iperf3 test')
    observer.add_scenario_argument(
            '--bandwidth', default='1M',
            help='the bandwidth (bits/s) of iperf3 test ')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be '
            'performed (histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, scenario_name)

    scenario = network_jitter.build(
                      args.server_entity,
                      args.client_entity,
                      args.server_ip,
                      args.server_port,
                      args.duration,
                      args.num_flows,
                      args.tos,
                      args.bandwidth,
                      args.post_processing_entity)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
