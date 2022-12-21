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

"""This executor builds or launches the *service_data_transfer* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
This scenario launches one TCP iperf3 flow with the specified parameters
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import service_data_transfer


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the source entity for the iperf3 traffic')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the destination entity for the iperf3 traffic')
    observer.add_scenario_argument(
            '--server-ip', required=True,
            help='server ip address for the iperf3 traffic')
    observer.add_scenario_argument(
            '--server-port', type=int, default=7001,
            help='server port for the iperf3 traffic (default : 7001)')
    group = observer.scenario_group.add_mutually_exclusive_group(required=True)
    group.add_argument(
            '--duration', type=int,
            help='duration of iperf3 transmission (in seconds)')
    group.add_argument(
            '--file-size', help='size of the file to transmit (in bytes). '
            'The value must be stricly higher than 1 MB')
    observer.add_scenario_argument(
            '--tos', default=0,
            help='set the ToS field of the TCP iperf3 traffic (e.g. 0x04)')
    observer.add_scenario_argument(
            '--mtu', type=int, default=1400,
            help='set the MTU of the TCP iperf3 traffic (in bytes, e.g. 1400)')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, service_data_transfer.SCENARIO_NAME)

    scenario = service_data_transfer.build(
            args.server_entity,
            args.client_entity,
            args.server_ip,
            args.server_port,
            args.duration,
            args.file_size,
            args.tos,
            args.mtu,
            args.post_processing_entity,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
