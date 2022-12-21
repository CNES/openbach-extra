#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2023 CNES
#
#
#   This file is part of the OpenBACH testbed.
#
#
#   OpenBACH is a free software : you can redistribute it and/or modify it under
#   the terms of the GNU General Public License as published by the Free Software
#   Foundation, either version 3 of the License, or (at your option) any later
#   version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
#   details.
#
#   You should have received a copy of the GNU General Public License along with
#   this program. If not, see http://www.gnu.org/licenses/.

"""This executor builds and launches the *service_vpn* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
It permits to create a VPN between 2 agents with Wireguard or OpenVPN.

The platform running this scenario is supposed to have an architecture
which looks likes the following :

+-----------+                       +----------------------+     +--------------------+                       +-----------+
|  Client   |                       |      Client VPN      |<--->|     Server VPN     |                       |  Server   |
|           |                       |   (client_entity*)   |     |  (server_entity*)  |                       |           |
+-----------+                       +----------------------+     +--------------------+                       +-----------+
|           |                       |                      |     |                    |                       |           |
|           |<--(client_ext_ipv4)-->|       client_int_ipv4|<--->|server_int_ipv4     |<--(server_ext_ipv4)-->|           |
+-----------+                       +----------------------+     +--------------------+                       +-----------+

* 'client' and 'server' stands for traffic generation and reception.

The VPN tunnel will be created between the 'server_entity' and the
'client_entity' based on the parameters 'server-tunnel-ipv4/port' and
'client-tunnel-ipv4/port'.

"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import service_vpn


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
        '--server-entity', required=True,
        help='Name of the server entity')
    observer.add_scenario_argument(
        '--client-entity', required=True,
        help='Name of the client entity')
    observer.add_scenario_argument(
        '--server-ext-ipv4', required=True,
        help="IPv4 network address (in CIDR format) of the server's LAN (aka external side).")
    observer.add_scenario_argument(
        '--client-ext-ipv4', required=True,
        help="IPv4 network address (in CIDR format) of the client's LAN (aka external side).")
    observer.add_scenario_argument(
        '--server-int-ipv4', required=True,
        help='IP address of the server')
    observer.add_scenario_argument(
        '--client-int-ipv4', required=True,
        help='IP address of the client')
    observer.add_scenario_argument(
        '--server-tun-ipv4', default=service_vpn.SERVER_TUN_IP_DEFAULT,
        help='Tun IP address of the server for OpenVPN Tun IP/CIDR for Wireguard')
    observer.add_scenario_argument(
        '--client-tun-ipv4', default=service_vpn.CLIENT_TUN_IP_DEFAULT,
        help='Tun IP address of the client for OpenVPN Tun IP/CIDR for Wireguard')
    observer.add_scenario_argument(
        '--server-tun-port', type=int, default=1194,
        help='Listening port of the server for the VPN tunnel')
    observer.add_scenario_argument(
        '--client-tun-port', type=int, default=1194,
        help='Listening port of the client for the VPN tunnel')
    observer.add_scenario_argument(
        '--vpn', choices=["wireguard", "openvpn"],
        default="openvpn", help='VPN to test')
    observer.add_scenario_argument(
        '--opvpn-protocol', choices=["udp", "tcp"],
        default="udp", help='OpenVPN protocol (ignored with Wireguard)')
    observer.add_scenario_argument(
        '--duration', type=int, default=0,
        help='Duration of the VPN tunnel application, leave blank for endless running.')

    args = observer.parse(argv, service_vpn.SCENARIO_NAME)

    scenario = service_vpn.build(
        args.server_entity,
        args.client_entity,
        args.server_ext_ipv4,
        args.client_ext_ipv4,
        args.server_int_ipv4,
        args.client_int_ipv4,
        args.server_tun_ipv4,
        args.client_tun_ipv4,
        args.server_tun_port,
        args.client_tun_port,
        args.vpn,
        args.opvpn_protocol,
        args.duration,
        scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
