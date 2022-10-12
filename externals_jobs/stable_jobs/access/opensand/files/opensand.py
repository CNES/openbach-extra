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

import re
import sys
import json
import select
import socket
import signal
import syslog
import os.path
import argparse
import tempfile
import ipaddress
import threading
import subprocess

import collect_agent
import py_opensand_conf


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


def run_entity(temp_dir, bin_dir, infrastructure, topology,
               profile=None, addr='127.0.0.1', logs_port=63000, stats_port=63001):
    global LOG_RCV
    global STAT_RCV
    global PROC

    opensand = os.path.join(bin_dir, 'opensand')

    subprocess.run([opensand, '-g', temp_dir])
    xsd = py_opensand_conf.fromXSD(os.path.join(temp_dir, 'infrastructure.xsd'))
    xml = py_opensand_conf.fromXML(xsd, infrastructure)

    # Bypass collector settings to redirect traffic through this job
    storage = xml.get_root().get_component('storage')
    storage.get_parameter('enable_collector').get_data().set(True)
    storage.get_parameter('collector_address').get_data().set(addr)
    storage.get_parameter('collector_logs').get_data().set(logs_port)
    storage.get_parameter('collector_probes').get_data().set(stats_port)

    infrastructure = os.path.join(temp_dir, 'infrastructure.xml')
    py_opensand_conf.toXML(xml, infrastructure)

    command = [opensand, '-i', infrastructure, '-t', topology]
    if profile is not None:
        command.extend(['-p', profile])

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


def parse_probe(value):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def forward_stat(payload, src_addr, src_port):
    data = iter(payload.decode().split())
    timestamp = int(next(data))
    values = { name: parse_probe(value) for name, value in grouper(data, 2) }
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
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/opensand/opensand_rstats_filter.conf'):
        parser = argparse.ArgumentParser(
            description='Set up the network configuration and launch an OpenSAND entity',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        parser.add_argument(
            'infrastructure', type=str,
            help='Path to the XML file of the infrastructure',
        )
        parser.add_argument(
            'topology', type=str,
            help='Path to the XML file of the topology',
        )
        parser.add_argument(
            '--profile', type=str,
            help='Path to the XML file of the profile. Required '
            'for all entities except the satellite.',
        )

        parser.add_argument(
            '--output-addr',
            type=str,
            default='127.0.0.1',
            help='The internal output address (format: "ADDRESS")',
        )
        parser.add_argument(
            '--logs-port',
            type=udp_port,
            default=63000,
            help='The internal logs UDP port',
        )
        parser.add_argument(
            '--stats-port',
            type=udp_port,
            default=63001,
            help='The internal stats UDP port',
        )
        parser.add_argument(
            '--bin-dir',
            type=str,
            default='/usr/bin/',
            help='The directory of OpenSAND binaries',
        )

        args = parser.parse_args()

        with tempfile.TemporaryDirectory(prefix='openbach_opensand_') as tmp:
            run_entity(
                    tmp, args.bin_dir,
                    args.infrastructure,
                    args.topology,
                    args.profile,
                    args.output_addr,
                    args.logs_port,
                    args.stats_port)
