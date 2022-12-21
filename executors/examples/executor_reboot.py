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


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder import Scenario
from scenario_builder.helpers.network.fping import fping_measure_rtt
from scenario_builder.helpers.admin.reboot import reboot


SCENARIO_DESCRIPTION="""This scenario is a wrapper of
        - fping job
        - reboot subscenario
        """
SCENARIO_NAME="""reboot_scenario"""


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument('--entity', required=True, help='Name of the entity we want to reboot')
    observer.add_scenario_argument('--ping-destination', default='127.0.0.1', help='Destination of fping (IP address)')
    observer.add_scenario_argument('--kernel', default=None, help='Kernel on which we want to reboot. No kernel: reboot on the default kernel. Kernel name can be found in /boot/grub/grub.cfg. It will be for example : "Linux 4.4.0-194-generic", so "Linux\ 4.4.0-194-generic" in command line')

    args = observer.parse(argv, SCENARIO_NAME)

    scenario_global = Scenario(args.scenario_name, SCENARIO_DESCRIPTION)

    first_fping = fping_measure_rtt(scenario_global, args.entity, args.ping_destination, duration=5)

    start_reboot_sub_scenario = scenario_global.add_function('start_scenario_instance', wait_finished=first_fping)
    sub_scenario = Scenario("reboot_sub_scenario", "Scenario with reboot function")
    reboot(sub_scenario, args.entity, args.kernel)
    start_reboot_sub_scenario.configure(sub_scenario)

    second_fping = fping_measure_rtt(scenario_global, args.entity, args.ping_destination, duration=5, wait_finished=[start_reboot_sub_scenario])

    observer.launch_and_wait(scenario_global)

if __name__ == '__main__':
    main()
