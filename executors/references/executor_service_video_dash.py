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

"""This executor builds or launches the *service_video_dash* scenario
from from /openbach-extra/apis/scenario_builder/scenarios/
It launches one DASH flow with the specified parameters
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import service_video_dash


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the source entity which sends the DASH traffic')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the entity which receives the DASH traffic')
    observer.add_scenario_argument(
            '--server-ip', required=True,
            help='source ip address for the DASH traffic')
    observer.add_scenario_argument(
            '--duration',type=int, default=60,
            help='duration of DASH traffic transmission in seconds')
    observer.add_scenario_argument(
            '--protocol', default='http/2',
            help='protocol used by DASH. Possible values are http/1.1 and http/2')
    observer.add_scenario_argument(
            '--tornado_port', type=int, default=5301,
            help='Port used by the Tornado Server to get statistics from the DASH client (Default: 5301)')
    observer.add_scenario_argument(
            '--launch-server', action='store_true',
            help='Launch an Apache2 server for the server agent. Optional. Default : False')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, service_video_dash.SCENARIO_NAME)

    scenario = service_video_dash.build(
            args.server_entity,
            args.client_entity,
            args.server_ip,
            args.duration,
            args.protocol,
            args.tornado_port,
            args.launch_server,
            args.post_processing_entity,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
