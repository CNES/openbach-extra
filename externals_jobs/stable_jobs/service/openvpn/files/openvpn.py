#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2020 CNES
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
'''

import collect_agent
import syslog
import os
import sys
import argparse
import subprocess
import time
import signal
from functools import partial
import psutil



DESCRIPTION = ("This job relies on OpenVPN program to launch openvpn daemon as server or client. " 
               "Its is used to build a routed VPN tunnel between two remote hosts in p2p mode. This job "
               "supports conventionnal encryption using a pre-shared secret key. It also allows " 
               "to setup non-encrypted TCP/UDP tunnels"
               )

PROTOCOL='udp'
PORT=1194
DEVICE='tun0'
SERVER_TUN_IP='10.8.0.1'
CLIENT_TUN_IP='10.8.0.2'
TUN_IP = '\'{}\' if server mode, else \'{}\' for client mode'
LOCAL_TUN_IP = TUN_IP.format(SERVER_TUN_IP, CLIENT_TUN_IP)
REMOTE_TUN_IP = TUN_IP.format(CLIENT_TUN_IP, SERVER_TUN_IP)
# pre-shared secret file which was generated with openvpn --genkey --secret secret.key
SECRET_PATH = '/opt/openbach/agent/jobs/openvpn/secret.key'


def connect_to_collect_agent():
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/openvpn/'
            'openvpn_rstats_filter.conf')
    if not success:
        message = 'Error connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


def build_cmd(mode, local_ip, protocol, local_port, tun_device, local_tun_ip, 
              remote_tun_ip, pass_tos, no_security):
    p = 'udp'
    if protocol == 'tcp':
       p = 'tcp-client'
       if mode == 'server':
          p = 'tcp-server'
    cmd = ['openvpn', '--local', local_ip, '--proto', p, '--lport', str(local_port)]
    if local_tun_ip == LOCAL_TUN_IP:
       local_tun_ip = CLIENT_TUN_IP
       if mode == 'server':
          local_tun_ip = SERVER_TUN_IP
    if remote_tun_ip == REMOTE_TUN_IP:
       remote_tun_ip = SERVER_TUN_IP
       if mode == 'server':
          remote_tun_ip = CLIENT_TUN_IP
          
    cmd.extend(['--dev-type', 'tun', '--dev', tun_device, '--ifconfig', local_tun_ip, remote_tun_ip])
    if pass_tos:
       cmd.extend(['--passtos'])
    cmd.extend(['--topology', 'p2p'])
    if no_security:
       cmd.extend(['--auth', 'none', '--cipher', 'none'])
    else:
       cmd.extend(['--secret', SECRET_PATH, '--auth', 'SHA256', '--cipher', 'AES-256-CBC'])
    return cmd


def server(local_ip, protocol, local_port, tun_device, local_tun_ip, 
           remote_tun_ip, pass_tos, no_security):
    connect_to_collect_agent()
    cmd = build_cmd('server', local_ip, protocol, local_port, tun_device, local_tun_ip, 
                    remote_tun_ip, pass_tos, no_security)
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when starting openvpn: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    p.wait()

    
def client(local_ip, protocol, local_port, tun_device, local_tun_ip, remote_tun_ip, pass_tos, 
           no_security, server_ip, server_port):
    connect_to_collect_agent()
    cmd = build_cmd('client', local_ip, protocol, local_port, tun_device, local_tun_ip, 
                    remote_tun_ip, pass_tos, no_security)
    if protocol == 'tcp':
       protocol = 'tcp-client'
    cmd.extend(['--remote', server_ip, str(server_port), protocol])
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when starting openvpn: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    p.wait()


if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description=DESCRIPTION, 
                 formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
            'local_ip', type=str,
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
             help=('Set the TOS field of the tunnel packet to what ' 
                   'the payload TOS is.')
    )
    
    parser.add_argument(
            '-no_sec', '--no_security', action='store_true', 
             help=('Disable authentification and encryption. (It must be same ' 
                   'on server and client)') 
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
    # Set subparsers options to automatically call the right
    # function depending on the chosen subcommand
    parser_server.set_defaults(function=server)
    parser_client.set_defaults(function=client)

    # Get args and call the appropriate function
    args = vars(parser.parse_args())
    main = args.pop('function')
    main(**args)
   
