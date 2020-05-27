#!/usr/bin/env python

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

"""Example of scenarios composition.

Data is transmitted from a server to a client
The test reports
 - The evolution of the received goodput
 - The time needed to receive 10%, 50% and 100% of the file

+-----------+     +-----------------------+     +-----------+
| data      |<--->| loss                  |<--->| data      |
| server    |     | limitation            |     | client    |
+-----------+     +-----------------------+     +-----------+
|  server_ip|     |                       |     |client_ip  |
|           |     |              midbox_if|     |           |
+-----------+     +-----------------------+     +-----------+
| entity:   |     | entity:               |     | entity:   |
|  server   |     |  midbox (middle-box)  |     |  client   |
+-----------+     +-----------------------+     +-----------+

OpenBACH parameters:
 - entity_pp : entity where the post-processing will be performed
 - project_name : the name of the project

Specific scenario parameters:
 - midbox_if : interface on which the loss pattern is applied 
 - operation : 'apply', 'clear'
          Choose apply to add configuration or clear to delete 
          existing ones
 - loss_model : 'random', 'state', 'gemodel' 
          packets loss model to use (only for apply operation) 
 - loss_model_paramaters' : packets loss model parameters to use 
          (only for apply operation). 
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_configure_link


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', '--configure-link-entity', '-e', required=True,
            help='Name of the entity where configure link should run')
    observer.add_scenario_argument(
            '--middlebox-interfaces', '--interfaces', '-m', required=True,
            help='Comma-separated list of the network interfaces to emulate link on on the middlebox')
    observer.add_scenario_argument(
            '--operation', choices=['apply', 'clear'], required=True,
            help='Choose apply to add configuration or clear to delete existing ones')
    observer.add_scenario_argument(
            '--loss-model', '-l', choices=['random', 'state', 'gemodel'],
            default='random', help='Packets loss model to use (only for apply operation)')
    observer.add_scenario_argument(
            '--loss-model-parameters', '-p', default=[0.0], type=float, nargs='+',
            help='Packets loss model parameters to use (only for apply operation).')

    args = observer.parse(argv)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            args.operation,
            bandwidth='300M',
            delay=1,
            loss_model=args.loss_model,
            loss_model_params=args.loss_model_parameters)
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            args.operation,
            bandwidth='300M',
            delay=1,
            loss_model=args.loss_model,
            loss_model_params=args.loss_model_parameters)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
