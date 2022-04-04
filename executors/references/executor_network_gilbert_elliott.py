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

"""This executor builds or launches the *network_gilbert_elliott* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
It measures the network packet loss rate.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_gilbert_elliott

# TODO how many t and l ?


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='Name of the entity which receives the traffic')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='Name of the entity which sends the traffic')
    observer.add_scenario_argument(
            '--server-interface', required=True,
            help='IP address of the traffic receiver')
    observer.add_scenario_argument(
            '--client-interface', required=True,
            help='IP address of the traffic sender')
    observer.add_scenario_argument(
            '--duration', type=int, default=10,
            help='Duration of the capture (seconds)')
    #TODO needed
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be '
            'performed (histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, network_gilbert_elliott.SCENARIO_NAME)

    scenario = network_gilbert_elliott.build(
                      args.server_entity,
                      args.client_entity,
                      args.server_interface,
                      args.client_interface,
                      args.duration,
                      args.post_processing_entity,
                      scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
