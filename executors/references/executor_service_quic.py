#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import service_quic

"""This executors builds or launches *service_quic* scenario
from /openbach_extra/api/scenario_builder/scenarios/"""

def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the server entity on which to run quic server')
    observer.add_scenario_argument(
            '--server-ip', required=True,
            help='The IP address of the server')
    observer.add_scenario_argument(
            '--server-port', default=4433,
            help='The port of the server to connect to/listen on')
    observer.add_scenario_argument(
            '--server-implementation', required=True,
            help='The QUIC implementation to run by the server. Possible values are: ngtcp2, picoquic, quicly')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the client entity on which to run quic client')
    observer.add_scenario_argument(
            '--client-implementation', required=True,
            help='The QUIC implementation to run by the client. Possible values are: ngtcp2, picoquic, quicly')
    observer.add_scenario_argument(
            '--resources', required=True,
            help='Comma-separed list of resources to fetch in parallel over concurrent streams')
   
    observer.add_scenario_argument(
            '--download-dir',
            help='The path to the directory to save downloaded resources')
    observer.add_scenario_argument(
            '--server-log-dir',
            help='The path to the directory to save server\'s logs')
    observer.add_scenario_argument(
            '--client-log-dir',
            help='The path to the directory to save client\'s logs')
    observer.add_scenario_argument(
            '--nb-runs', default=1,
            help='The number of times resources will be downloaded')
    observer.add_scenario_argument(
            '--post-processing-entity', 
            help='The entity where the post-processing will be performed '
                 '(histogram/time-series jobs must be installed) if defined')


    args = observer.parse(argv, service_quic.SCENARIO_NAME)

    scenario = service_quic.build(
            args.server_entity,
            args.server_ip,
            args.server_port,
            args.server_implemenation,
            args.client_entity,
            args.client_implementation,
            args.resources,
            args.nb_runs,
            args.download_dir,
            args.server_log_dir,
            args.client_log_dir,
            args.post_processing_entity,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
