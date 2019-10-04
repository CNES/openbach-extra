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
from scenario_builder.scenarios import service_traffic_mix

"""This scenario launches the *RT_AGM_global* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """

def main():
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity_pp', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')
    observer.add_scenario_argument(
            '--extra_args_traffic', default="", help='Extra arguments for traffic generation')

    args = observer.parse()

    scenario = service_traffic_mix.build(
            args.entity_pp,
            args.extra_args_traffic)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()