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

"""This executor builds or launches the *network_sr_tunnel* scenario from
/openbach-extra/apis/scenario_builder/scenarios/. It launches 'sr_tunnel'
in 2 entities. sr_tunnel is a program which implements a Selective Repeat
algorithm at the IP level within a TUN/TAP tunnel. A good illustration of
the algorithm implemented is given here :
https://www2.tkn.tu-berlin.de/teaching/rn/animations/gbn_sr/.

The platform running this scenario is supposed to have an architecture
which looks likes the following :

+------------------------+                   +------------------------+
|     client_entity      |                   |     server_entity      |
|                        |                   |                        |
+------------------------+                   +------------------------+
|                        |                   |server_tun_ip           |
|           client_tun_ip|<----------------->|server_ip*              |
+------------------------+                   +------------------------+


* 'client_tun_ip' and 'server_tun_ip' stands for the IPv4 address which will be 
associated to the tun0 interfaces that will be created. 'server_ip' stands for the
IPv4 address of the server (address of a 'physical' interface, not tun0) that the 
client will use to communicate with the server.

**Important Note** : The traffic needs to be sent to the 'tun0' interfaces in order to
activate the Selective Repeate process.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_sr_tunnel


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='Entity which will listen on incoming connections to create the SR tunnel.')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='Entity which will connect to the server and then, crezte the SR tunnel.')
    observer.add_scenario_argument(
            '--server-ip', required=True,
            help='The IPv4 address of the server ("physical" interface address, not "tun0")')
    observer.add_scenario_argument(
            '--server-tun-ip', required=True,
            help='IPv4/mask address of the local "tun0" interface that will be created on the server side.')
    observer.add_scenario_argument(
            '--client-tun-ip', required=True,
            help='IPv4/mask address of the local "tun0" interface that will be created on the client side.')
    observer.add_scenario_argument(
            '--server-port', type=int,
            help='Port of the server (Default 30001)')
    observer.add_scenario_argument(
            '--trace', default='/opt/openbach/agent/jobs/sr_tunnel/sr_tunnel.log',
            help='The path to store the trace of packets on both entities.')
    observer.add_scenario_argument(
            '--server-drop', type=int,
            help='Emulate link-layer losses by dropping sent packet on server side (expressed in percentage of drop from 0 to 100)')
    observer.add_scenario_argument(
            '--client-drop', type=int,
            help='Emulate link-layer losses by dropping sent packet on client side (expressed in percentage of drop from 0 to 100)')
    observer.add_scenario_argument(
            '--server-burst', type=int,
            help='Average burst size on server side. GE model for losses. Default is 1 if -d is set')
    observer.add_scenario_argument(
            '--client-burst', type=int,
            help='Average burst size on client side. GE model for losses. Default is 1 if -d is set')
    observer.add_scenario_argument(
            '--duration', type=int, default=0,
            help='Duration of the SR tunnel application, leave blank for endless running.')

    args = observer.parse(argv, network_sr_tunnel.SCENARIO_NAME)

    scenario = network_sr_tunnel.build(
            args.server_entity,
            args.client_entity,
            args.server_ip,
            args.server_tun_ip,
            args.client_tun_ip,
            args.server_port,
            args.trace,
            args.server_drop,
            args.client_drop,
            args.server_burst,
            args.client_burst,
            args.duration,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()

