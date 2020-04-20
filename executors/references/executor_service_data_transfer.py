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

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import service_data_transfer

"""This scenario launches one TCP iperf3 flow with the specified parameters"""

def main():
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the destination entity for the iperf3 traffic')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the source entity for the iperf3 traffic')
    observer.add_scenario_argument(
            '--server-ip', required=True,
            help='destination ip address for the iperf3 traffic')
    observer.add_scenario_argument(
            '--server-port', required=True,
            help='destination port for the iperf3 traffic (e.g. 5201)')
    observer.add_scenario_argument(
            '--file-size', required=True,
            help='size of the file to transmit (in bytes) - must be set to 0 if '
            'the end of the transfer is defined by the duration parameter')
    observer.add_scenario_argument(
            '--tos', required=True,
            help='set the ToS field of the TCP iperf3 traffic (e.g. 0x04)')
    observer.add_scenario_argument(
            '--mtu', required=True,
            help='set the MTU of the TCP iperf3 traffic (in bytes, e.g. 1400)')
    observer.add_scenario_argument(
            '--duration', required=True,
            help='duration of iperf3 transmission (in seconds) - must be set to ' 
            'an integer value even if the file_size parameter defines the end of'
            'transfer (the value will then be ignored)')
    observer.add_scenario_argument(
            '--entity-pp', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')

    args = observer.parse()

    scenario = service_data_transfer.build(
            args.server_entity,
            args.client_entity,
            args.server_ip,
            args.server_port,
            args.duration,
            args.file_size,
            args.tos,
            args.mtu,
            args.entity_pp,
            scenario_name="service_data_transfer")

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
