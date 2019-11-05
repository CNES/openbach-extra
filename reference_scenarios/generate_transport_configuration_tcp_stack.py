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

"""This scenario builds and launches the *configure_tcp_stack* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import transport_configuration_tcp_stack


def main(scenario_name=None, argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', required=True,
            help='Name of the openabch entity to apply configuration on')
    observer.add_scenario_argument(
            '--cc', '--congestion_control',
            help='Congestion control name')
    observer.add_scenario_argument(
            '--iface', '--network_interface',
            help='Interface to configure segementation offload on')
    observer.add_scenario_argument(
            '--dest_ip', '--destination_ip',
            help='Ip address of the destination network')
    observer.add_scenario_argument(
            '--gw_ip', '--gateway_ip',
            help='Ip address of the gateway')
    observer.add_scenario_argument(
            '--dev', '--device',
            help='Output device name')
    observer.add_scenario_argument(
            '--icwnd', '--initcwnd', type=str, default=0,
            help='Initial congestion window size for connections to specified destination')
    observer.add_scenario_argument(
            '--irwnd', '--initrwnd', type=str, default=0,
            help='Initial receive window size for connections to specified destination')
    
    args = observer.parse(argv, scenario_name)
    route = {'destination_ip':args.dest_ip,
             'gateway_ip':args.gw_ip,
             'device':args.dev,
             'initcwnd':args.icwnd,
             'initrwnd':args.irwnd,
             }

    scenario = transport_configuration_tcp_stack.build(
                args.entity,
                args.cc,
                args.iface,
                route
    )
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
