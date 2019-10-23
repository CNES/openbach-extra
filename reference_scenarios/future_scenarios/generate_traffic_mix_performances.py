#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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

"""This script launches the *traffic mix performances* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import traffic_mix_performances


def main(scenario_name='generate_traffic_mix_performances', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server', '--server-entity', required=True,
            help='name of the entity for the server of the global tests')
    observer.add_scenario_argument(
            '--iface',  help='The iperf3/nuttcp server port for data')
    observer.add_scenario_argument(
            '--cc', default='cubic', help='The port of nuttcp server for signalling')
    observer.add_scenario_argument(
            '--init_cwnd', default=10, help='duration of each delay, rate,   scenario (s)')
    observer.add_scenario_argument(
            '--extra_args_traffic', help='duration of each delay, rate,   scenario (s)')
    observer.add_scenario_argument(
            '--entity_pp', help='The entity where the post-processing will be '
            'performed (histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, scenario_name)

    scenario = traffic_mix_performances.build(
                      args.server,
                      args.iface,
                      args.cc,
                      args.init_cwnd,
                      args.extra_args_traffic,
                      args.entity_pp)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
