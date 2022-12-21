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

""" Helpers of openvpn job """
from ..utils import filter_none

PROTOCOL = 'udp'
PORT = 1194
SERVER_TUN_IP = '10.10.10.1'
CLIENT_TUN_IP = '10.10.10.2'
DEVICE = 'tun0'


def openvpn(
        scenario, server_entity, server_ip, client_entity, client_ip=None, no_bind_client=False,
        server_port=PORT, client_port=PORT, protocol=PROTOCOL,
        server_tun_dev=DEVICE, client_tun_dev=DEVICE,
        server_tun_ip=SERVER_TUN_IP, client_tun_ip=CLIENT_TUN_IP,
        pass_tos=False, no_security=False, tcp_nodelay=False,
        ping=0, ping_restart=-1, route_through_vpn_client=None, route_through_vpn_server=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    launch_server = scenario.add_function(
        'start_job_instance',
        wait_finished=wait_finished,
        wait_launched=wait_launched,
        wait_delay=wait_delay)

    param_server = filter_none(local_ip=server_ip,
                               protocol=protocol,
                               local_port=server_port,
                               tun_device=server_tun_dev,
                               local_tun_ip=server_tun_ip,
                               remote_tun_ip=client_tun_ip,
                               pass_tos=pass_tos,
                               no_security=no_security,
                               tcp_nodelay=tcp_nodelay,
                               ping=ping,
                               ping_restart=ping_restart,
                               route_through_vpn=route_through_vpn_server
                               )
    launch_server.configure(
        'openvpn', server_entity, offset=0,
        server={},
        **param_server)

    launch_client = scenario.add_function(
        'start_job_instance',
        wait_launched=[launch_server],
        wait_delay=2)

    param_client = filter_none(local_ip=client_ip,
                               protocol=protocol,
                               local_port=client_port,
                               tun_device=client_tun_dev,
                               local_tun_ip=client_tun_ip,
                               remote_tun_ip=server_tun_ip,
                               pass_tos=pass_tos,
                               no_security=no_security,
                               tcp_nodelay=tcp_nodelay,
                               ping=ping,
                               ping_restart=ping_restart,
                               route_through_vpn=route_through_vpn_client
                               )

    launch_client.configure(
        'openvpn', client_entity, offset=0,
        client={
            'server_ip': server_ip,
            'server_port': server_port,
            'nobind': no_bind_client,
        },
        **param_client)

    return [launch_server, launch_client]


def openvpn_behind_nat(
        scenario, server_entity, server_ip, client_entity, remote_point_ip, client_ip=None, no_bind_client=False,
        server_port=PORT, client_port=PORT, protocol=PROTOCOL,
        server_tun_dev=DEVICE, client_tun_dev=DEVICE,
        server_tun_ip=SERVER_TUN_IP, client_tun_ip=CLIENT_TUN_IP,
        pass_tos=False, no_security=False, tcp_nodelay=False,
        ping=0, ping_restart=-1, route_through_vpn_client=None, route_through_vpn_server=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    launch_server = scenario.add_function(
        'start_job_instance',
        wait_finished=wait_finished,
        wait_launched=wait_launched,
        wait_delay=wait_delay)

    param_server = filter_none(local_ip=server_ip,
                               protocol=protocol,
                               local_port=server_port,
                               tun_device=server_tun_dev,
                               local_tun_ip=server_tun_ip,
                               remote_tun_ip=client_tun_ip,
                               pass_tos=pass_tos,
                               no_security=no_security,
                               tcp_nodelay=tcp_nodelay,
                               ping=ping,
                               ping_restart=ping_restart,
                               route_through_vpn=route_through_vpn_server
                               )
    launch_server.configure(
        'openvpn', server_entity, offset=0,
        server={},
        **param_server)

    launch_client = scenario.add_function(
        'start_job_instance',
        wait_launched=[launch_server],
        wait_delay=2)

    param_client = filter_none(local_ip=client_ip,
                               protocol=protocol,
                               local_port=client_port,
                               tun_device=client_tun_dev,
                               local_tun_ip=client_tun_ip,
                               remote_tun_ip=server_tun_ip,
                               pass_tos=pass_tos,
                               no_security=no_security,
                               tcp_nodelay=tcp_nodelay,
                               ping=ping,
                               ping_restart=ping_restart,
                               route_through_vpn=route_through_vpn_client
                               )

    launch_client.configure(
        'openvpn', client_entity, offset=0,
        client={
            'server_ip': remote_point_ip,
            'server_port': server_port,
            'nobind': no_bind_client,
        },
        **param_client)

    return [launch_server, launch_client]
