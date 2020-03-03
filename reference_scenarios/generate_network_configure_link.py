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

"""This scenario builds and launches the *network_configure_link* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_configure_link


def main(scenario_name='configure_link', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', '-e', required=True,
            help='Name of the entity emulating the link')
    observer.add_scenario_argument(
            '--ifaces', '--network_interfaces', required=True,
            help='Commat-separed list of the network interfaces to emulate link on')
    observer.add_scenario_argument(
            '--mode', choices=['ingress', 'egress', 'all'], required=True,
            help='Targeted direction: ingress, egress or all')
    observer.add_scenario_argument(
            '--operation', choices=['apply', 'clear'], required=True, 
            help='Choose apply to add configuration or clear to delete existing ones')
    observer.add_scenario_argument(
            '--bandwidth', type=str,
            help='The link bandwidth in Mbps or Kbps, expressed as [value][M|K] '
                  '(only for apply operation)')
    observer.add_scenario_argument(
            '--lm', '--loss_model', choices=['random', 'state', 'gemodel'],
            default='random', help='Packets loss model to use (only for apply operation)')
    observer.add_scenario_argument(
            '--lmp', '--loss_model_paramaters', default=0.0, type=float, nargs='*',
            help='Packets loss model parameters to use (only for apply operation). Warning: This must not be the last argument of the scenario'
            'This could be used as follows:'
            '--lm random --lmp 1 --bandwidth 300M --delay 1 ; to add 1% random losses'
            '--lm gemodel --lmp 1.8 64.5 100 0 --bandwidth 300M --delay 1 ; to add P(g|g)= 0.982, P(g|b)= 0.645, P(b|b)= 0.355, P(b|g)= 0.018'
            '(see [RFC6534] for more details)')
    observer.add_scenario_argument(
            '--delay', type=int, default=0,
            help='Delay to add to packets, in ms (only for apply operation)')
    observer.add_scenario_argument(
            '--jitter', type=int, default=0,
            help='Delay variation, in ms (only for apply operation)')
    observer.add_scenario_argument(
            '--dd', '--delay_distribution',
            choices=['uniform', 'normal', 'pareto', 'paretonormal'], default='normal',
            help='Distribution to use to choose delay value (only for apply operation)')
    observer.add_scenario_argument(
            '--buffer_size', type=int, default=10000,
            help='Size of the buffer for qlen and netem limit parameter (default=10000)')

    args = observer.parse(argv, scenario_name)

    scenario = network_configure_link.build(
                args.entity,
                args.ifaces,
                args.mode,
                args.operation,
                args.bandwidth,
                args.delay,
                args.jitter,
                args.dd,
                args.lm,
                args.lmp,
                args.buffer_size
    )
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
