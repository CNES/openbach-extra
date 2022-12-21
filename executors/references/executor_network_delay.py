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

"""This executor builds or launches the *network_delay* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
It launches network delay test comparison with fping and d-itg.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_delay


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the entity for the srv of the RTT tests')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the entity for the client of the RTT tests')
    observer.add_scenario_argument(
            '--server-ip', required=True, help='destination ip address and target of the pings')
    observer.add_scenario_argument(
            '--client-ip', required=True, help='IP address of source of pings and packets')
    observer.add_scenario_argument(
            '--duration', type=int, default=10, help='duration of delay scenario in seconds')
    observer.add_scenario_argument(
            '--simultaneous', action='store_true',
            help='option whether or not the test is simultaneous. Default sequential')
    observer.add_scenario_argument(
            '--max-synchro-off', type=float,
            help='maximal offset difference in milliseconds where we have to do a NTP '
            'resynchronization; if omitted, no NTP checks are performed')
    observer.add_scenario_argument(
            '--synchronization-timeout', type=float, default=60.0,
            help='maximal synchronization duration in seconds')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be '
            'performed (histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, network_delay.SCENARIO_NAME)

    scenario = network_delay.build(
                      args.server_entity,
                      args.client_entity,
                      args.server_ip,
                      args.client_ip,
                      args.duration,
                      args.simultaneous,
                      args.max_synchro_off,
                      args.synchronization_timeout,
                      args.post_processing_entity,
                      scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
