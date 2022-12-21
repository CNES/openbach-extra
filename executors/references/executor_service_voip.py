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

"""This executor builds or launches the *service_voip* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
It launches one VoIP flow with the specified parameters.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import service_voip


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the destination entity for the VoIP traffic')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the source entity for the VoIP traffic')
    observer.add_scenario_argument(
            '--server-ip', required=True,
            help='destination ip address for the VoIP traffic')
    observer.add_scenario_argument(
            '--client-ip', required=True,
            help='source ip address for the VoIP traffic')
    observer.add_scenario_argument(
            '--server-port', type=int, default=10000,
            help='destination port for the VoIP traffic')
    observer.add_scenario_argument(
            '--duration', type=int, default=10,
            help='duration of VoIP transmission in seconds')
    observer.add_scenario_argument(
            '--codec', choices=['G.711.1', 'G.711.2', 'G.723.1', 'G.729.2', 'G.729.3'], default='G.711.1',
            help='codec used by the VoIP traffic')
    observer.add_scenario_argument(
            '--max-synchro-off', type=float,
            help='maximal offset difference in milliseconds where we have to do a NTP '
            'resynchronization; if omitted, no NTP checks are performed')
    observer.add_scenario_argument(
            '--synchronization-timeout', type=float, default=60.0,
            help='maximal synchronization duration in seconds')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, service_voip.SCENARIO_NAME)

    scenario = service_voip.build(
            args.server_entity,
            args.client_entity,
            args.server_ip,
            args.client_ip,
            args.server_port,
            args.duration,
            args.codec,
            args.max_synchro_off,
            args.synchronization_timeout,
            args.post_processing_entity,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
