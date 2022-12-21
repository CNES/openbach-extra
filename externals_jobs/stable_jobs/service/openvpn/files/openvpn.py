#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2023 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.


"""Sources of the Job openvpn"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Francklin SIMO <francklin.simo@viveris.fr>
 * Romain GUILLOTEAU <romain.guilloteau@viveris.fr>
'''

import sys
import syslog
import struct
import socket
import argparse
import subprocess

import collect_agent


DESCRIPTION = (
        "This job relies on OpenVPN program to launch openvpn daemon as server or client. "
        "Its is used to build a routed VPN tunnel between two remote hosts in p2p mode. This job "
        "supports conventionnal encryption using a pre-shared secret key. It also allows "
        "to setup non-encrypted TCP/UDP tunnels"
)

PROTOCOL = 'udp'
PORT = 1194
DEVICE = 'tun0'
SERVER_TUN_IP = '10.8.0.1'
CLIENT_TUN_IP = '10.8.0.2'
TUN_IP = '\'{}\' if server mode, else \'{}\' for client mode'
LOCAL_TUN_IP = TUN_IP.format(SERVER_TUN_IP, CLIENT_TUN_IP)
REMOTE_TUN_IP = TUN_IP.format(CLIENT_TUN_IP, SERVER_TUN_IP)
# pre-shared secret file which was generated with openvpn --genkey --secret secret.key
SECRET_PATH = '/opt/openbach/agent/jobs/openvpn/secret.key'

# By Trenton McKinney: https://stackoverflow.com/a/33750650


def cidr_to_netmask(cidr):
    network, net_bits = cidr.split('/')
    host_bits = 32 - int(net_bits)
    netmask = socket.inet_ntoa(struct.pack('!I', (1 << 32) - (1 << host_bits)))
    return network, netmask


def build_cmd(mode, local_ip, protocol, tun_device, local_tun_ip,
              remote_tun_ip, pass_tos, no_security, tcp_nodelay, ping, ping_restart, route_through_vpn):
    p = 'udp'
    if protocol == 'tcp':
        p = 'tcp-client'
        if mode == 'server':
            p = 'tcp-server'
    cmd = ['openvpn', '--proto', p]
    if local_ip:
        cmd.extend(['--local', local_ip])
    if protocol == 'tcp':
        if tcp_nodelay:
            cmd.extend(["--tcp-nodelay"])

    if local_tun_ip == LOCAL_TUN_IP:
        local_tun_ip = CLIENT_TUN_IP
        if mode == 'server':
            local_tun_ip = SERVER_TUN_IP
    if remote_tun_ip == REMOTE_TUN_IP:
        remote_tun_ip = SERVER_TUN_IP
        if mode == 'server':
            remote_tun_ip = CLIENT_TUN_IP

    cmd.extend(['--dev-type', 'tun', '--dev', tun_device,
                '--ifconfig', local_tun_ip, remote_tun_ip])
    if pass_tos:
        cmd.extend(['--passtos'])
    cmd.extend(['--topology', 'p2p'])
    if no_security:
        cmd.extend(['--auth', 'none', '--cipher', 'none'])
    else:
        cmd.extend(['--secret', SECRET_PATH, '--auth',
                    'SHA256', '--cipher', 'AES-256-CBC'])

    if ping > 0:
        cmd.extend(["--ping", str(ping)])
    if ping_restart >= 0:
        cmd.extend(["--ping-restart", str(ping_restart)])

    if route_through_vpn is not None:
        ip, netmask = cidr_to_netmask(route_through_vpn)
        cmd.extend(["--route", ip, netmask, "vpn_gateway"])

    return cmd


def server(local_ip, protocol, local_port, tun_device, local_tun_ip,
           remote_tun_ip, pass_tos, no_security, tcp_nodelay, ping, ping_restart, route_through_vpn):
    cmd = build_cmd('server', local_ip, protocol, tun_device, local_tun_ip,
                    remote_tun_ip, pass_tos, no_security, tcp_nodelay, ping, ping_restart, route_through_vpn)
    cmd.extend(['--lport', str(local_port)])
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when starting openvpn: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    p.wait()


def client(local_ip, protocol, local_port, tun_device, local_tun_ip, remote_tun_ip, pass_tos,
           no_security, server_ip, server_port, tcp_nodelay, nobind, ping, ping_restart, route_through_vpn):
    cmd = build_cmd('client', local_ip, protocol, tun_device, local_tun_ip,
                    remote_tun_ip, pass_tos, no_security, tcp_nodelay, ping, ping_restart, route_through_vpn)
    if protocol == 'tcp':
        protocol = 'tcp-client'
    cmd.extend(['--remote', server_ip, str(server_port), protocol])
    if nobind:
        cmd.extend(["--nobind"])
    else:
        cmd.extend(['--lport', str(local_port)])
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when starting openvpn: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    p.wait()


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/openvpn/openvpn_rstats_filter.conf'):
        # Argument parsing
        parser = argparse.ArgumentParser(
                description=DESCRIPTION,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            '-local-ip', '--local-ip', type=str,
            help='The IP address used to communicate with peer'
        )
        parser.add_argument(
            '-proto', '--protocol', choices=['udp', 'tcp'], default=PROTOCOL,
            help=('The transport protocol to use to communicate with peer. '
                      '(It must be same on server and client)')
        )
        parser.add_argument(
            '-lport', '--local_port', type=int, default=PORT,
            help='The port number used for bind'
        )
        parser.add_argument(
            '-dev', '--tun_device', type=str, default=DEVICE,
            help='The name of virtual TUN device acting as VPN endpoint'
        )
        parser.add_argument(
            '-ltun_ip', '--local_tun_ip', type=str, default=LOCAL_TUN_IP,
            help='The IP address of the local VPN endpoint'
        )

        parser.add_argument(
            '-rtun_ip', '--remote_tun_ip', type=str, default=REMOTE_TUN_IP,
            help='The IP address of the remote VPN endpoint'
        )
        parser.add_argument(
            '-pass_tos', '--pass_tos', action='store_true',
            help='Set the TOS field of the tunnel packet to what the payload TOS is.'
        )

        parser.add_argument(
            '-no_sec', '--no_security', action='store_true',
            help='Disable authentification and encryption. (It must be same on server and client)'
        )

        parser.add_argument(
            '-tcp-nodelay', '--tcp-nodelay', action='store_true',
            help='Disable Nagle algorithm'
        )

        parser.add_argument(
            '-ping', '--ping', type=int, default=0,
            help='Ping remote over the TCP/UDP control channel if no '
                 'packets have been sent for at least n seconds'
        )

        parser.add_argument(
            '-ping-restart', '--ping-restart', type=int, default=-1,
            help='Causes OpenVPN to restart after n seconds pass without '
                 'reception of a ping or other packet from remote'
        )

        parser.add_argument(
            '-route-through-vpn', '--route-through-vpn', type=str,
            help='Add route with vpn interface as gateway (format: IP/Netmask)'
        )

        # Sub-commands to split server and client mode
        subparsers = parser.add_subparsers(
            title='Subcommand mode',
            help='Choose the OpenVPN mode (server mode or client mode)'
        )
        parser_server = subparsers.add_parser('server', help='Run in server mode')
        parser_client = subparsers.add_parser('client', help='Run in client mode')
        parser_client.add_argument(
            'server_ip', type=str,
            help='The IP address of the server'
        )
        parser_client.add_argument(
            '-rport', '--server_port', type=int, default=PORT,
            help='The port number that the server is bound to'
        )
        parser_client.add_argument(
            '-nobind', '--nobind', action='store_true',
            help='Do not bind to local address and port',
        )
        # Set subparsers options to automatically call the right
        # function depending on the chosen subcommand
        parser_server.set_defaults(function=server)
        parser_client.set_defaults(function=client)

        # Get args and call the appropriate function
        args = vars(parser.parse_args())
        main = args.pop('function')
        main(**args)
