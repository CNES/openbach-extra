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

"""Example of scenario composition.

A specific TCP stack modification is applied 
The test reports
 - The evolution of the received goodput
 - The time needed to receive 10%, 50% and 100% of the file

+-----------+   +-------------+   +-------------+   +-----------+
| data      |<->| PEPS        |<->| PEPC        |<->| data      |
| server    |   |             |   |             |   | client    |
+-----------+   +-------------+   +-------------+   +-----------+
|  server_ip|   |peps_ip_in   |   |pepc_ip_in   |   |client_ip  |
|           |   |  peps_ip_out|   |  peps_ip_out|   |           |
+-----------+   +-------------+   +-------------+   +-----------+
| entity:   |   | entity:     |   | entity:     |   | entity:   |
|  server   |   |   peps      |   |  pepc       |   |  client   |
+-----------+   +-------------+   +-------------+   +-----------+

OpenBACH parameters:
 - entity_pp : entity where the post-processing will be performed
 - project_name : the name of the project

Specific scenario parameters:
 - tcp_wmem_min 
 - tcp_wmem_default 
 - tcp_wmem_max 
 - tcp_rmem_min 
 - tcp_rmem_default 
 - tcp_rmem_max 
 - core_wmem_default 
 - core_wmem_max 
 - core_rmem_default 
 - core_rmem_max 
 - initcwnd : Initial congestion window size for connections to specified destination
 - initrwnd : Initial receive window size for connections to specified destination

Other parameters:
 - server-IP : IP address of the server
 - client-IP : IP address of the client
 - peps-ip-in : IP address of the PEPS towards the server
 - peps-ip-out : IP address of the PEPS towards PEPC
 - pepc-ip-in : IP address of the PEPC towards PEPS
 - pepc-ip-out : IP address of the PEPC towards the client
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import transport_tcp_stack_conf


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity-pep-server', required=True,
            help='Name of the openabch entity to apply configuration on')
    observer.add_scenario_argument(
            '--client-ip', required=True,
            help='Ip address of the destination network')
    observer.add_scenario_argument(
            '--server-gateway-ip', required=True,
            help='Ip address of the gateway for the server')
    observer.add_scenario_argument(
            '--entity-pep-client', required=True,
            help='Name of the openabch entity to apply configuration on')
    observer.add_scenario_argument(
            '--server-ip', required=True,
            help='Ip address of the source network')
    observer.add_scenario_argument(
            '--client-gateway-ip', required=True,
            help='Ip address of the gateway for the client')
    observer.add_scenario_argument(
            '--tcp_wmem_min', type=int,
            help='The tcp_wmem_min field')
    observer.add_scenario_argument(
            '--tcp_wmem_default', type=int,
            help='The tcp_wmem_default field')
    observer.add_scenario_argument(
            '--tcp_wmem_max', type=int,
            help='The tcp_wmem_max field')
    observer.add_scenario_argument(
            '--tcp_rmem_min', type=int,
            help='The tcp_rmem_min field')
    observer.add_scenario_argument(
            '--tcp_rmem_default', type=int,
            help='The tcp_rmem_default field')
    observer.add_scenario_argument(
            '--tcp_rmem_max', type=int,
            help='The tcp_rmem_max field')
    observer.add_scenario_argument(
            '--core_wmem_default', type=int,
            help='The core_wmem_default field')
    observer.add_scenario_argument(
            '--core_wmem_max', type=int,
            help='The core_wmem_max field')
    observer.add_scenario_argument(
            '--core_rmem_default', type=int,
            help='The core_rmem_default field')
    observer.add_scenario_argument(
            '--core_rmem_max', type=int,
            help='The core_rmem_max field')
    observer.add_scenario_argument(
            '--icwnd', '--initcwnd', type=str, default=10,
            help='Initial congestion window size for connections to specified destination')
    observer.add_scenario_argument(
            '--irwnd', '--initrwnd', type=str, default=10,
            help='Initial receive window size for connections to specified destination')
    observer.add_scenario_argument(
            '--operation', choices=["add", "change", "delete"], default="change",
            help='Select the operation to apply')

    args = observer.parse(argv)

    tcp_params = {
            'tcp_wmem_min': args.tcp_wmem_min,
            'tcp_wmem_default': args.tcp_wmem_default,
            'tcp_wmem_max': args.tcp_wmem_max,
            'tcp_rmem_min': args.tcp_rmem_min,
            'tcp_rmem_default': args.tcp_rmem_default,
            'tcp_rmem_max': args.tcp_rmem_max,
            'core_wmem_default': args.core_wmem_default,
            'core_wmem_max': args.core_wmem_max,
            'core_rmem_default': args.core_rmem_default,
            'core_rmem_max': args.core_rmem_max,
            'congestion_control': 'CUBIC',
    }
    tcp_params = {k: v for k, v in tcp_params.items() if v is not None}

    scenario = transport_tcp_stack_conf.build(
            args.entity_pep_server,
            tcp_params,
            {}
            route={
                'destination_ip': args.client_ip,
                'gateway_ip': args.server_gateway_ip,
                'operation': args.operation,
                'device': None,
                'initcwnd': args.icwnd,
                'initrwnd': args.irwnd,
            })
    observer.launch_and_wait(scenario)

    scenario = transport_tcp_stack_conf.build(
            args.entity_pep_client,
            tcp_params,
            {}
            route={
                'destination_ip': args.server_ip,
                'gateway_ip': args.client_gateway_ip,
                'operation': args.operation,
                'device': None,
                'initcwnd': args.icwnd,
                'initrwnd': args.irwnd,
            })
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
