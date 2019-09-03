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
from scenario_builder.scenarios.RT_AQM_scenarios import RT_AQM_global

"""This scenario launches the *RT_AGM_global* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """

def main():
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--gateway_scheduler', required=True,
            help='name of the entity to place scheduler')
    observer.add_scenario_argument(
            '--interface_scheduler', required=True,
            help='interface on the entity to place scheduler')
    observer.add_scenario_argument(
            '--path_scheduler', required=True,
            help='path to the configuration file of the scheduler, on the entity')
    observer.add_scenario_argument(
            '--entity_pp', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')
    observer.add_scenario_argument(
            '--extra_args', default="", help='Extra arguments')
    observer.add_scenario_argument(
            '--reset_scheduler', action="store_true", help='Reset the scheduler at the end of the simulation')
    observer.add_scenario_argument(
            '--reset_iptables', action="store_true", help='Reset the iptables rules at the end of the simulation')

    args = observer.parse()
    extra_args = []

    try:
        file = open(args.extra_args,"r")
        for line in file:
            if len(line) < 10:
                continue
            if line[0] != '#':
                extra_args.append(line.split())
        file.close()
    except (OSError, IOError):
        print("Cannot open args file, exiting")
        return

    scenario = RT_AQM_global.build(
            args.gateway_scheduler,
            args.interface_scheduler,
            args.path_scheduler,
            args.entity_pp,
            extra_args,
            args.reset_scheduler,
            args.reset_iptables)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()