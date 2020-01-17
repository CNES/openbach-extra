#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
#
# OpenSAND is an emulation testbed aiming to represent in a cost effective way a
# satellite telecommunication system for research and engineering activities.
#
#
# Copyright © 2019 TAS
#
#
# This file is part of the OpenSAND testbed.
#
#
# OpenSAND is free software : you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.
#
#

"""
@file     opensand.py
@brief    Set up the network configuration and launch an OpenSAND entity.
@author   Aurélien DELRIEU <aurelien.delrieu@viveris.fr>
"""


import argparse
import opensand_network.opensand_network_utils as onu
import subprocess
import signal
import netifaces as ni
import ipaddress
import socket
import threading
import select
import syslog
import collect_agent
import json
import re
import sys


DFLT_TAPNAME = 'opensand_tap'
DFLT_BRNAME = 'opensand_br'
PATTERN = re.compile(r'\[(?P<timestamp>[^\]]+)\]\[\s*(?P<log_level>\w+)\]\[(?P<log_name>[^:]+)\](?P<log_message>.*)')
LEVELS = {
    'DEBUG': syslog.LOG_DEBUG,
    'INFO': syslog.LOG_INFO,
    'NOTICE': syslog.LOG_NOTICE,
    'WARNING': syslog.LOG_WARNING,
    'ERROR': syslog.LOG_ERR,
    'CRITICAL': syslog.LOG_CRIT,
}
PROC = None
LOG_RCV = None
STAT_RCV = None


def run_entity(command, addr, logs_port, stats_port):
    global LOG_RCV
    global STAT_RCV
    global PROC

    if command is None:
        return
    command.extend([
        '-r', addr,
        '-l', str(logs_port),
        '-s', str(stats_port),
    ])

    signal.signal(signal.SIGINT, stop_entity)
    signal.signal(signal.SIGTERM, stop_entity)

    LOG_RCV = MessageReceiver(addr, logs_port, forward_log)
    STAT_RCV = MessageReceiver(addr, stats_port, forward_stat)

    LOG_RCV.start()
    STAT_RCV.start()
    PROC = subprocess.Popen(command, stderr=subprocess.PIPE)

    PROC.wait()
    if PROC.returncode:
        error = PROC.stderr.read().decode()
        if any(
                err in error
                for err in {'File exists', 'No such process'}
                ):
            message = 'WARNING: {} exited with non-zero return value ({}): {}'.format(
                command, PROC.returncode, error)
            collect_agent.send_log(syslog.LOG_WARNING, message)
            sys.exit(0)
        else:
            message = 'ERROR: {} exited with non-zero return value ({})'.format(
                command, PROC.returncode)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)


def stop_entity(signum, frame):
    global LOG_RCV
    global STAT_RCV
    if PROC is not None:
        PROC.send_signal(signal.SIGKILL)

    if LOG_RCV is not None:
        LOG_RCV.stop()
        LOG_RCV = None
    if STAT_RCV is not None:
        STAT_RCV.stop()
        STAT_RCV = None


def grouper(iterable, n):
    args = [iter(iterable)] * n
    return zip(*args)


def forward_stat(payload, src_addr, src_port):
    data = iter(payload.decode().split())
    timestamp = int(next(data))
    values = { name: json.loads(value) for name, value in grouper(data, 2) }
    collect_agent.send_stat(timestamp, **values)


def forward_log(payload, src_addr, src_port):
    global PATTERN

    match = PATTERN.match(payload.decode().rstrip())
    if not match:
        return
    level = LEVELS.get(match.group(2))
    if level is None:
        return
    collect_agent.send_log(
        level, 
        '[{}]{}'.format(match.group(3), match.group(4)),
    )


class MessageReceiver(threading.Thread):

    DEFAULT_TIMEOUT = 0.020 # in millisecond
    DEFAULT_BUFFERLEN = 4096

    def __init__(self, addr, port, on_reception, timeout=DEFAULT_TIMEOUT, bufferlen=DEFAULT_BUFFERLEN):
        super().__init__()
        self.addr = addr
        self.port = port

        self._on_reception = on_reception
        self._timeout = timeout
        self._bufferlen = bufferlen

        self._stop_evt = threading.Event()

    def stop(self):
        self._stop_evt.set()
        self.join()

    def run(self):
        rcv_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        rcv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        rcv_sock.bind((self.addr, self.port))
        
        while not self._stop_evt.is_set():
            readable, _, _ = select.select([ rcv_sock ], [], [], self._timeout)
            for sock in readable:
                payload, (src_addr, src_port) = sock.recvfrom(self._bufferlen)
                if not payload:
                    continue
                self._on_reception(payload, src_addr, src_port)

        rcv_sock.close()


def ip_address(text):
    '''
    Check a text represents an IP address

    Args:
        text   text to check
    '''
    addr = ipaddress.ip_address(text)
    return text


def ip_address_mask(text):
    '''
    Check a text represents an IP address and a net digit

    Args:
        text   text to check
    '''
    addr = ipaddress.ip_network(text, False)
    return text


def existing_iface(text):
    '''
    Check a text represents an existing interface

    Args:
        text   text to check
    '''
    if text not in ni.interfaces():
        raise ValueError('No "{}" interface'.format(text))
    return text


def udp_port(text):
    '''
    Check a text represents a UDP port

    Args:
        text   text to check
    '''
    value = int(text)
    if value <= 0:
        raise ValueError('UDP port must be strictly positive')
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Set up the network configuration and launch an OpenSAND entity',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    action_cmd = parser.add_subparsers(
        dest='action_type',
        metavar='action_type',
        help='the OpenSAND action type',
    )
    action_cmd.required = True

    # Network parsers
    net_parser = action_cmd.add_parser(
        'network',
        help='Configure the network for an OpenSAND entity',
    )
    net_parser.add_argument(
        '-t',
        '--tap-name',
        type=str,
        default=DFLT_TAPNAME,
        help='the TAP interface name (default: {})'.format(DFLT_TAPNAME),
    )
    net_parser.add_argument(
        '-b',
        '--bridge-name',
        type=str,
        default=DFLT_BRNAME,
        help='the bridge name (default: {})'.format(DFLT_BRNAME),
    )

    subaction_cmd = net_parser.add_subparsers(
        dest='action',
        metavar='action',
        help='the action to perform',
    )
    subaction_cmd.required = True

    ip_parser = subaction_cmd.add_parser(
        onu.IP_TYPE,
        help='create interfaces to connect an IP terrestrial network',
    )
    ip_parser.add_argument(
        'address_mask',
        type=ip_address_mask,
        help='the terrestrial network address (format: "ADDRESS/NET_DIGIT")',
    )

    eth_parser = subaction_cmd.add_parser(
        onu.ETH_TYPE,
        help='create interfaces to connect an Ethernet terrestrial network',
    )
    eth_parser.add_argument(
        'interface',
        type=existing_iface,
        help='the terrestrial network interface',
    )

    clear_parser = subaction_cmd.add_parser(
        'clear',
        help='clear interfaces to connect terrestrial network',
    )

    # Run parsers
    run_parser = action_cmd.add_parser(
        'run',
        help='Run an OpenSAND entity',
    )
    run_parser.add_argument(
        '--conf-dir',
        type=str,
        default='/etc/opensand/',
        help='The directory of the OpenSAND entity configuration',
    )
    run_parser.add_argument(
        '--output-addr',
        type=str,
        default='127.0.0.1',
        help='The internal output address (format: "ADDRESS")',
    )
    run_parser.add_argument(
        '--logs-port',
        type=udp_port,
        default=63000,
        help='The internal logs UDP port',
    )
    run_parser.add_argument(
        '--stats-port',
        type=udp_port,
        default=63001,
        help='The internal stats UDP port',
    )
    run_parser.add_argument(
        '--bin-dir',
        type=str,
        default='/usr/bin/',
        help='The directory of OpenSAND binaries',
    )

    run_entity_cmd = run_parser.add_subparsers(
        dest='entity',
        metavar='entity',
        help='the OpenSAND entity type',
    )
    run_entity_cmd.required = True

    run_st_parser = run_entity_cmd.add_parser(
        'st',
        help='Satellite Terminal',
    )
    run_gw_parser = run_entity_cmd.add_parser(
        'gw',
        help='Gateway',
    )
    run_sat_parser = run_entity_cmd.add_parser(
        'sat',
        help='Satellite',
    )
    run_gw_net_acc_parser = run_entity_cmd.add_parser(
        'gw-net-acc',
        help='Gateway (network and access layers)',
    )
    run_gw_phy_parser = run_entity_cmd.add_parser(
        'gw-phy',
        help='Gateway (physical layer)',
    )

    for p in [ run_st_parser, run_gw_parser, run_gw_net_acc_parser, run_gw_phy_parser ]:
        p.add_argument(
            'id',
            type=int,
            help='the OpenSAND entity identifier',
        )

    for p in [ run_st_parser, run_gw_parser, run_gw_phy_parser, run_sat_parser ]:
        p.add_argument(
            'emu_addr',
            type=ip_address,
            help='the emulation address (format: "ADDRESS")',
        )

    for p in [ run_gw_net_acc_parser, run_gw_phy_parser ]:
        p.add_argument(
            'interco_addr',
            type=ip_address,
            help='the remote interconnection address (format: "ADDRESS")',
        )

    for p in [ run_st_parser, run_gw_parser, run_gw_net_acc_parser ]:
        p.add_argument(
            '-t',
            '--tap-name',
            type=str,
            default=DFLT_TAPNAME,
            help='the TAP interface name (default: {})'.format(DFLT_TAPNAME),
        )

    args = parser.parse_args()

    collect_agent.register_collect(
        '/opt/openbach/agent/jobs/opensand/opensand_rstats_filter.conf',
    )

    if args.action_type == 'network':

        try:
            if args.action == onu.IP_TYPE:
                onu.create_tap_iface(args.tap_name)
                onu.set_up(args.tap_name)
                onu.create_bridge(args.bridge_name, [ args.tap_name ])
                onu.set_up(args.bridge_name)

                onu.add_address(args.bridge_name, args.address_mask)

                try:
                    ipaddress.IPv4Network(args.address_mask, False)
                    onu.enable_ipv4_forward()
                except ipaddress.AddressValueError:
                    pass
                try:
                    ipaddress.IPv6Network(args.address_mask, False)
                    onu.enable_ipv6_forward()
                except ipaddress.AddressValueError:
                    pass
              
            elif args.action == onu.ETH_TYPE:
                onu.create_tap_iface(args.tap_name)
                onu.set_up(args.tap_name)
                onu.create_bridge(args.bridge_name, [ args.tap_name, args.interface ])
                onu.set_up(args.bridge_name)

            elif args.action == 'clear':
                onu.delete_iface(args.bridge_name)
                onu.delete_iface(args.tap_name)
        except onu.NetworkUtilsError as err:
            collect_agent.send_message(syslog.LOG_ERR, str(err))
            sys.exit(-1)

    elif args.action_type == 'run':
        command = None
        if args.entity == 'sat':
            command = [
                '{}/{}'.format(args.bin_dir, args.entity),
                '-a', args.emu_addr,
                '-c', args.conf_dir,
            ]
        elif args.entity in [ 'st', 'gw' ]:
            command = [
                '{}/{}'.format(args.bin_dir, args.entity),
                '-i', str(args.id),
                '-a', args.emu_addr,
                '-t', args.tap_name,
                '-c', args.conf_dir,
            ]
        elif args.entity == 'gw-net-acc':
            command = [
                '{}/{}'.format(args.bin_dir, args.entity),
                '-i', str(args.id),
                '-t', args.tap_name,
                '-w', args.interco_addr,
                '-c', args.conf_dir,
            ]
        elif args.entity == 'gw-phy':
            command = [
                '{}/{}'.format(args.bin_dir, args.entity),
                '-i', str(args.id),
                '-a', args.emu_addr,
                '-w', args.interco_addr,
                '-c', args.conf_dir,
            ]
        else:
            collect_agent.send_message(
                syslog.LOG_ERR,
                'The OpenSAND entity "{}" is not handled by this script'.format(args.entity)
            )
            sys.exit(-1)

        run_entity(command, args.output_addr, args.logs_port, args.stats_port)
