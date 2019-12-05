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

PROC = None
LOG_RCV = None
STAT_RCV = None
PATTERN = re.compile(r'\[(?P<timestamp>[^\]]+)\]\[\s*(?P<log_level>\w+)\] (?P<log_name>[^:]+): (?P<log_message>.*)')
LEVELS = {
    'DEBUG': syslog.LOG_DEBUG,
    'INFO': syslog.LOG_INFO,
    'NOTICE': syslog.LOG_NOTICE,
    'WARNING': syslog.LOG_WARNING,
    'ERROR': syslog.LOG_ERR,
    'CRITICAL': syslog.LOG_CRIT,
}


def run_entity(command, addr, logs_port, stats_port):
    global LOG_RCV
    global STAT_RCV
    global OPB_FWD
    global PROC

    if command is None:
        return
    command += ' -r {} -l {} -s {}'.format(addr, logs_port, stats_port)

    signal.signal(signal.SIGINT, stop_entity)
    signal.signal(signal.SIGTERM, stop_entity)

    collect_agent.register_collect(
        '/opt/openbach/agent/jobs/opensand/',
        'opensand_rstats_filter.conf',
    )
    LOG_RCV = MessageReceiver(addr, logs_port, forward_log)
    STAT_RCV = MessageReceiver(addr, stats_port, forward_stat)

    LOG_RCV.start()
    STAT_RCV.start()
    PROC = subprocess.Popen(command.split())

    PROC.wait()
    PROC = None
    STAT_RCV.stop()
    LOG_RCV.stop()


def stop_entity(signum, frame):
    global LOG_RCV
    global STAT_RCV
    if PROC is not None:
        PROC.send_signal(signum)

    if LOG is not None:
        LOG.stop()
        LOG = None
    if STAT is not None:
        STAT.stop()
        STAT = None


def grouper(iterable, n):
    args = [iter(iterable)] * n
    return itertools.izip(*args)


def forward_stat(payload, src_addr, src_port):
    data = iter(payload.decode().split())
    timestamp = int(next(data))
    values = { name: json.loads(value) for name, value in grouper(data, 2) }
    collect_agent.send_stat(timestamp, **values)


def forward_log(payload, src_addr, src_port):
    global PATTERN
    
    match = PATTERN.match(payload.decode())
    if not match:
        return
    level = LEVELS.get(match.group(1))
    if level is None:
        return
    collect_agent.send_message(
        level, 
        '{}: {}'.format(match.group(2), match.group(3)),
    )


class MessageReceiver(threading.Thread):

    DEFAULT_TIMEOUT = 0.020 # in millisecond
    DEFAULT_BUFFERLEN = 4096

    def __init__(self, addr, port, on_reception, timeout=DEFAULT_TIMEOUT, bufferlen=DEFAULT_BUFFERLEN):
        self.addr = addr
        self.port = port

        self._on_reception = on_reception
        self._timeout = timeout
        self._bufferlen = bufferlen

        self._stop = threading.Event()

    def stop(self):
        self._stop.set()
        self.join()

    def run(self):
        rcv_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        rcv_sock.setopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        rcv_sock.bind(self.addr, self.port)
        
        while not self._stop.is_set():
            readable, _, _ = select.select([ rcv_sock ], [], [], self._timeout)
            for sock in readable:
                payload, (src_addr, src_port) = sock.recvfrom(self._bufferlen)
                if not payload:
                    continue
                self._on_reception(payload, src_addr, src_port)

        rcv_sock.close()


def ipv4_address_netdigit(text):
    '''
    Check a text represents an IPv4 address and a net digit

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
        dest='action',
        metavar='action',
        help='the OpenSAND action',
    )
    action_cmd.required = True

    # Network parsers
    net_parser = action_cmd.add_parser(
        'network',
        help='Configure the network for an OpenSAND entity',
    )
    net_entity_cmd = net_parser.add_subparsers(
        dest='entity',
        metavar='entity',
        help='the OpenSAND entity type',
    )
    net_entity_cmd.required = True

    net_st_parser = net_entity_cmd.add_parser(
        'st',
        help='Satellite Terminal',
    )
    net_gw_parser = net_entity_cmd.add_parser(
        'gw',
        help='Gateway',
    )
    net_sat_parser = net_entity_cmd.add_parser(
        'sat',
        help='Satellite',
    )
    net_gw_net_acc_parser = net_entity_cmd.add_parser(
        'gw_net_acc',
        help='Gateway (network and access layers)',
    )
    net_gw_phy_parser = net_entity_cmd.add_parser(
        'gw_phy',
        help='Gateway (physical layer)',
    )

    # Run parsers
    run_parser = action_cmd.add_parser(
        'run',
        help='Run an OpenSAND entity',
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
        'gw_net_acc',
        help='Gateway (network and access layers)',
    )
    run_gw_phy_parser = run_entity_cmd.add_parser(
        'gw_phy',
        help='Gateway (physical layer)',
    )

    for p in [ net_st_parser, net_gw_parser, net_gw_net_acc_parser, net_gw_phy_parser,
               run_st_parser, run_gw_parser, run_gw_net_acc_parser, run_gw_phy_parser ]:
        p.add_argument(
            '-i',
            '--id',
            type=int,
            required=True,
            help='the OpenSAND entity identifier',
        )

    for p in [ net_st_parser, net_gw_parser, net_gw_net_acc_parser ]:
        p.add_argument(
            '-t',
            '--type',
            choices=onu.ALL_TYPES,
            default=onu.DEFAULT_TYPE,
            help='the type of the terrestrial network',
        )
        p.add_argument(
            '-n',
            '--net-iface',
            type=existing_iface,
            required=True,
            help='the terrestrial network interface',
        )
        p.add_argument(
            '--net-addr',
            type=ipv4_address_netdigit,
            default=None,
            help='the terrestrial network address (format: "ADDRESS/NET_DIGIT")',
        )

    for p in [ net_st_parser, net_gw_parser, net_gw_phy_parser, net_sat_parser ]:
        p.add_argument(
            '-e',
            '--emu-iface',
            type=existing_iface,
            required=True,
            help='the emulation interface',
        )

    for p in [ net_st_parser, net_gw_parser, net_gw_phy_parser, net_sat_parser,
               run_st_parser, run_gw_parser, run_gw_phy_parser, run_sat_parser ]:
        p.add_argument(
            '-a',
            '--emu-addr',
            type=ipv4_address_netdigit,
            required=True,
            help='the emulation address (format: "ADDRESS/NET_DIGIT")',
        )

    for p in [ net_gw_net_acc_parser, net_gw_phy_parser ]:
        p.add_argument(
            '-o',
            '--interco-iface',
            type=existing_iface,
            required=True,
            help='the interconnection interface',
        )
        p.add_argument(
            '--interco-addr',
            type=ipv4_address_netdigit,
            required=True,
            help='the interconnection address (format: "ADDRESS/NET_DIGIT")',
        )

    for p in [ run_gw_net_acc_parser, run_gw_phy_parser ]:
        p.add_argument(
            '--interco-addr',
            type=ipv4_address_netdigit,
            required=True,
            help='the remote interconnection address (format: "ADDRESS")',
        )

    for p in [ net_st_parser, net_gw_parser, net_gw_net_acc_parser ]:
        p.add_argument(
            '--int-addr',
            type=ipv4_address_netdigit,
            default=None,
            help='the internal address (format: "ADDRESS/NET_DIGIT")',
        )

    for p in [ net_st_parser, net_gw_parser, net_gw_net_acc_parser, net_gw_phy_parser, net_sat_parser ]:
        p.add_argument(
            '-r',
            '--revert',
            action='store_false',
            dest='configure',
            help='revert the current network configuration',
        )

    for p in [ run_st_parser, run_gw_parser, run_gw_net_acc_parser, run_gw_phy_parser, run_sat_parser ]:
        p.add_argument(
            '-c',
            '--conf',
            type=str,
            required=True,
            help='The directory of the OpenSAND entity configuration',
        )
        p.add_argument(
            '--output-addr',
            type=str,
            default='127.0.0.1',
            help='The output address (format: "ADDRESS")',
        )
        p.add_argument(
            '--logs-port',
            type=udp_port,
            default=63000,
            help='The logs UDP port',
        )
        p.add_argument(
            '--stats-port',
            type=udp_port,
            default=63001,
            help='The stats UDP port',
        )
        p.add_argument(
            '--bin-dir',
            type=str,
            default='/usr/bin/',
            help='The directory of OpenSAND entities binaries',
        )

    args = parser.parse_args()
    if args.action == 'run':
        command = None
        if args.entity == 'sat':
            command = '{}/{} -a {} -c {}'.format(
                args.bin_dir,
                args.entity,
                args.emu_addr,
                args.conf,
            )
        elif args.entity in [ 'st', 'gw' ]:
            command = '{}/{} -i {} -a {} -t {}tap -c {}'.format(
                args.bin_dir,
                args.entity,
                args.id,
                args.emu_addr,
                args.id,
                args.conf,
            )
        elif args.entity == 'gw_net_acc':
            command = '{}/{} -i {} -t {}tap -w {} -c {}'.format(
                args.bin_dir,
                args.entity,
                args.id,
                args.id,
                args.interconnect_addr,
                args.conf,
            )
        elif args.entity == 'gw_phy':
            command = '{}/{} -i {} -a {} -w {} -c {}'.format(
                args.bin_dir,
                args.entity,
                args.id,
                args.emu_addr,
                args.interconnect_addr,
                args.conf,
            )

        run_entity(command, args.output_addr, args.logs_port, args.stats_port)

    elif args.action == 'network':
        if args.entity == 'sat':
            onu.host_sat(
                args.entity,
                args.emu_iface,
                args.emu_addr,
                args.configure,
            )

        elif args.entity in [ 'gw', 'st' ]:
            if args.type == onu.IP_TYPE:
                onu.host_ground_ip(
                    '{}{}'.format(args.entity, args.id),
                    args.emu_iface,
                    args.net_iface,
                    args.emu_addr,
                    args.net_addr,
                    args.int_addr,
                    args.configure,
                )

            elif args.type == onu.ETH_TYPE:
                onu.host_ground_eth(
                    '{}{}'.format(args.entity, args.id),
                    args.emu_iface,
                    args.net_iface,
                    args.emu_addr,
                    args.configure,
                )

            else:
                raise ValueError('Unexpected type value "{}"'.format(args.type))

        elif args.entity == 'gw_net_acc':
            if args.type == onu.IP_TYPE:
                onu.host_ground_net_acc_ip(
                    '{}{}'.format(args.entity, args.id),
                    args.interco_iface,
                    args.net_iface,
                    args.interco_addr,
                    args.net_addr,
                    args.int_addr,
                    args.configure,
                )

            elif args.type == onu.ETH_TYPE:
                onu.host_ground_net_acc_eth(
                    '{}{}'.format(args.entity, args.id),
                    args.interco_iface,
                    args.net_iface,
                    args.interco_addr,
                    args.configure,
                )

            else:
                raise ValueError('Unexpected type value "{}"'.format(args.type))

        elif args.entity == 'gw_phy':
            onu.host_ground_phy(
                '{}{}'.format(args.entity, args.id),
                args.emu_iface,
                args.interco_iface,
                args.emu_addr,
                args.interco_addr,
                args.configure,
            )
