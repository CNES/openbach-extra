#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2020 CNES
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
        '--server-ip', required=True,
        help='IP address of the server')
    observer.add_scenario_argument(
        '--client-ip', required=False,
        help='IP address of the client. Required for Wireguard')
    observer.add_scenario_argument(
        '--server-tun-port', type=int, default=1194,
        help='Listening port of the server for the VPN tunnel')
    observer.add_scenario_argument(
        '--client-tun-port', type=int, default=1194,
        help='Listening port of the client for the VPN tunnel')
    observer.add_scenario_argument(
        '--server-tun-ip', default=service_vpn.SERVER_TUN_IP_DEFAULT,
        help='Tun IP address of the server for OpenVPN Tun IP/CIDR for Wireguard')
    observer.add_scenario_argument(
        '--client-tun-ip', default=service_vpn.CLIENT_TUN_IP_DEFAULT,
        help='Tun IP address of the client for OpenVPN Tun IP/CIDR for Wireguard')
    observer.add_scenario_argument(
        '--vpn', choices=["wireguard", "openvpn"],
        default="openvpn", help='VPN to test')
    observer.add_scenario_argument(
        '--opvpn-protocol', choices=["udp", "tcp"],
        default="udp", help='OpenVPN protocol (ignored with Wireguard)')

    args = observer.parse(argv, service_vpn.SCENARIO_NAME)

    scenario = service_vpn.build(
        args.server_entity,
        args.client_entity,
        args.server_ip,
        args.client_ip,
        args.server_tun_port,
        args.client_tun_port,
        args.server_tun_ip,
        args.client_tun_ip,
        args.vpn,
        args.opvpn_protocol,
        scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
