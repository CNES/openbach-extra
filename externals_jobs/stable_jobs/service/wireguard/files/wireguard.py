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


"""Sources of the Job wireguard"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Romain GUILLOTEAU <romain.guilloteau@viveris.fr>
'''

import sys
import syslog
import signal
import argparse
import subprocess

import collect_agent


DESCRIPTION = """\
This job relies on Wireguard program to launch openvpn daemon as server or client.
Its is used to build a routed VPN tunnel between two remote hosts in p2p mode. This job
supports conventionnal encryption using a pre-shared secret key."""


def create_interface(tun_dev, tun_ip, private_key, listen_port, mtu):
    conf_file = '/tmp/{}.conf'.format(tun_dev)
    with open(conf_file, 'w') as f:
        f.write('[Interface]\n')
        f.write('PrivateKey = {}\n'.format(private_key))
        if listen_port:
            f.write('ListenPort = {}\n'.format(listen_port))
        f.write("\n")

    # Create interface
    cmd = ['ip', 'link', 'add',
           'dev', tun_dev, 'mtu', str(mtu), 'type', 'wireguard']
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when creating interface wireguard: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    p.wait()

    cmd = ['ip', 'addr', 'add', 'dev', tun_dev, tun_ip]
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when setting ip address: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    p.wait()

    cmd = ['wg', 'setconf', tun_dev, conf_file]
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when configuring interface: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    p.wait()

    cmd = ['ip', 'link', 'set', 'up', 'dev', tun_dev]
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when setting ip address: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    p.wait()

    signal.pause()


def peer(tun_dev, peer_pub_key, allowed_ips, endpoint, persistent_keepalive, remove):
    cmd = ["wg", "set", tun_dev, "peer", peer_pub_key]
    if remove:
        cmd.append("remove")
    else:
        if endpoint is not None:
            cmd.extend(["endpoint", endpoint])
        cmd.extend(["persistent-keepalive", str(persistent_keepalive)])
        if len(allowed_ips) > 0:
            cmd.extend(["allowed-ips", ','.join(allowed_ips)])

    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when setting interface: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    p.wait()


def command_line_parser():
    parser = argparse.ArgumentParser(
            description=DESCRIPTION,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            "-tun-dev", "--tun-dev",
            type=str, default="wg0",
            help="Name of the WireGuard interface")

    subparsers = parser.add_subparsers(
        title="Subcommand mode", required=True,
        help="Choose the action to apply: create an interface, add a peer, remove a peer, delete the interface")

    parser_create_interface = subparsers.add_parser(
        "create_interface", help="Create a new interface")

    parser_peer = subparsers.add_parser(
        "peer", help="Add, change or remove a peer to the existing interface")

    # Subparser for interface creation
    parser_create_interface.add_argument(
        'tun_ip', type=str,
        help='The IP/CIDR address to bind with the wireguard interface'
    )
    parser_create_interface.add_argument(
        'private_key', type=str,
        help='The private key created with wg genkey'
    )
    parser_create_interface.add_argument(
        '-listen-port', '--listen-port', type=int, default=0,
        help="The listen port (Default is a random value)"
    )
    parser_create_interface.add_argument(
        '-mtu', '--mtu', type=int, default=1420,
        help="MTU of the interface"
    )

    # Subparser for peer actions
    parser_peer.add_argument(
        'peer_pub_key', type=str,
        help='The Public key of the peers we want to communicate with'
    )
    parser_peer.add_argument(
        '-allowed-ips', '--allowed-ips', type=str, nargs='+', default=[],
        help='The IP/CIDR network allowed to communicate with this public key'
    )
    parser_peer.add_argument(
        '-endpoint', '--endpoint', type=str, default=None,
        help='<IP or hostname>:<port>. This endpoint will be updated automatically to the most recent source IP address and port of correctly authenticated packets from the peer.'
    )
    parser_peer.add_argument(
        '-persistent-keepalive', '--persistent-keepalive', type=int, default=0,
        help='Send a periodic keepalive with the period given. By default, this option is off'
    )

    parser_peer.add_argument(
        '-remove', '--remove', action='store_true',
        help="Remove the peer"
    )

    # Set subparsers options to automatically call the right
    # function depending on the chosen subcommand
    parser_create_interface.set_defaults(function=create_interface)
    parser_peer.set_defaults(function=peer)

    return parser


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/wireguard/wireguard_rstats_filter.conf'):
        # Get args and call the appropriate function
        args = vars(command_line_parser().parse_args())
        main = args.pop('function')
        main(**args)
