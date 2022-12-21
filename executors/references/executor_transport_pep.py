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

"""This executor runs the Pep job"""
import argparse 

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.helpers.transport import pep
from scenario_builder.scenarios import transport_pep


def main(argv=None):
    observer = ScenarioObserver()

    observer.add_scenario_argument(
            '--entity', '-e', required=True,
            help='Name of the entity on which to run pepsal')
    observer.add_scenario_argument(
            '-p', '--port', type=int, default=5000,
            help='The port PEPsal uses to listen for incoming connection')
    observer.add_scenario_argument(
            '-a', '--address', type=str, default="0.0.0.0",
            help='The address PEPsal uses to bind the listening socket')
    observer.add_scenario_argument(
            '-f', '--fastopen', action="store_true",
            help='Enable TCP FastOpen')
    observer.add_scenario_argument(
            '-c', '--maxconns', type=int, default=2112,
            help='The maximum number of simultaneous connections')
    observer.add_scenario_argument(
            '-g', '--gcc-interval', type=int, default=54000,
            help='The garbage collector interval')
    observer.add_scenario_argument(
            '-l', '--log-file', type=str, default="/var/log/pepsal/connections.log",
            help='The connections log path')
    observer.add_scenario_argument(
            '-t', '--pending-lifetime', type=int, default=18000,
            help='The pending connections lifetime')
    observer.add_scenario_argument(
            '-x', '--stop', action="store_true",
            help='If set, unset routing configuration')
    observer.add_scenario_argument(
            '-i', '--redirect-ifaces', type=str, default='',
            help="Redirect all traffic from incoming interfaces to PEPsal (admits multiple interfaces separated by ',' ' ')")
    observer.add_scenario_argument(
            '-s', '--redirect-src-ip', type=str, default='',
            help="Redirect all traffic with src IP to PEPsal (admits multiple IPs separated by ',' ' ')")
    observer.add_scenario_argument(
            '-d', '--redirect-dst-ip', type=str, default='',
            help="Redirect all traffic with dest IP to PEPsal (admits multiple IPs separated by ',' ' ')")
    observer.add_scenario_argument(
            '-m', '--mark', type=int, default=1,
            help='The mark used for routing packets to the PEP')
    observer.add_scenario_argument(
            '-T', '--table-num', type=int, default=100,
            help='The routing table number used for routing packets to the PEP')
    observer.add_scenario_argument(
            '--duration', type=int, default=0,
            help='Duration of the test in seconds. Leave blank for endless running.')


    args = observer.parse(argv, transport_pep.SCENARIO_NAME)

    scenario = transport_pep.build(
            args.entity,
            args.address,
            args.port,
            args.fastopen,
            args.maxconns,
            args.gcc_interval,
            args.log_file,
            args.pending_lifetime,
            args.stop,
            args.redirect_ifaces,
            args.redirect_src_ip,
            args.redirect_dst_ip,
            args.mark,
            args.table_num,
            args.duration)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
