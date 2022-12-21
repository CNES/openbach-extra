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

"""This executor builds and launches the *transport_tcpdump* scenario
from /openbach-extra/apis/scenario_builder/scenarios/

"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import transport_tcpdump
from scenario_builder.helpers.utils import filter_none


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', '-e', required=True,
            help='Name of the openbach entity to capture/analyze packets on')
    observer.add_scenario_argument(
            '--mode', '-m', choices=['capture', 'analyze', 'both'], required=True,
            help='Select a mode: \'capture\' for live capture or \'analyze\' for analyze a capture file')
    observer.add_scenario_argument(
            '--capture-file', '-f', required=True,
            help='Path to the file to save captured packets or to read packets to analyze (big files are not recommended: check .help of pcap_postprocessing job)')
    observer.add_scenario_argument(
            '--interface', '-i', default='any',
            help='Network interface to sniff (only for capture mode)')
    observer.add_scenario_argument(
            '--src-ip', '-A',
            help='Source IP address of packets to process')
    observer.add_scenario_argument(
            '--dst-ip', '-a',
            help='Destination IP address of packets to process')
    observer.add_scenario_argument(
            '--src-port', '-D', type=int,
            help='Source port number of packets to process')
    observer.add_scenario_argument(
            '--dst-port', '-d', type=int,
            help='Destination port number of packets to process')
    observer.add_scenario_argument(
            '--proto', '-p', choices=['udp', 'tcp'],
            help='Transport protocol of packets to process')
    observer.add_scenario_argument(
            '--duration', '-t', type=int,
            help='Duration in seconds of the capture (only for capture mode)')
    observer.add_scenario_argument(
            '--metrics-interval', '-T', type=int, default=500,
            help='Time period in ms to compute metrics (only used when packets are analyzed)')
    observer.add_scenario_argument(
            '--post-processing-entity', 
            help='The entity where the post-processing will be performed '
                 '(histogram/time-series jobs must be installed) if defined. ' 
                 '(only used when packets are analyzed)')

    
    args = observer.parse(argv, transport_tcpdump.SCENARIO_NAME)

    scenario = transport_tcpdump.build(
            args.entity,
            args.mode,
            args.capture_file,
            args.interface,
            args.src_ip,
            args.dst_ip,
            args.src_port,
            args.dst_port,
            args.proto,
            args.duration,
            args.metrics_interval,
            args.post_processing_entity,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()

