#!/usr/bin/env python3
# -*- coding: utf-8 -*- 

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
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


"""Sources for the job norm"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David FERNANDES <david.fernandes@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''

import os
import re
import ast
import time
import syslog
import argparse
import threading
import socketserver
from random import randint
from contextlib import suppress
from collections import defaultdict
from functools import total_ordering
from tempfile import NamedTemporaryFile

import pynorm
import collect_agent


END_OF_TRANSMISSION_EVENTS = {'NORM_TX_QUEUE_EMPTY', 'NORM_TX_FLUSH_COMPLETED'}


@total_ordering
class Element:
    def __init__(self, file_number, filepath, filename):
        self.file_number = file_number
        self.filepath = filepath
        self.filename = filename
        self.sent = False

    def __lt__(self, other):
        try:
            return self.file_number < other.file_number
        except AttributeError:
            return False

    def __eq__(self, other):
        try:
            return self.file_number == other.file_number
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.file_number)


class CustomUnixDatagramServer(socketserver.UnixDatagramServer):
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        self.report = None
        self.current_suffix = None
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)

    def server_close(self):
        """ Remove Unix socket on exit """
        fn = self.socket.getsockname()
        super().server_close()
        with suppress(FileNotFoundError):
            os.remove(fn)


class UDPUnixRequestHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        def load(line):
            for statistic in msg.split(' '):
                with suppress(ValueError):
                    key, value = statistic.split('>')
                    if key == 'suffix':
                        self.server.current_suffix = int(value)
                    else:
                        self.server.report[self.server.current_suffix].update(
                                {key: float(value)})

        msg = self.rfile.read().decode()[:-2]
        # Start of new message
        if not self.server.report and msg.startswith('Proto Info: REPORT'):
            self.server.report = defaultdict(dict)
            self.server.current_suffix = None
            load(msg)
        # End of message
        elif self.server.report and msg.startswith('Proto Info: ******'):
            if len(self.server.report) == 1:
                # Only None  to report. Report it
                stats = self.server.report[None]
                timestamp = int(stats['time'] * 1000)
                del(stats['time'])
                collect_agent.send_stat(timestamp, **stats)
            else:
                for suffix in filter(None, self.server.report):
                    stats = self.server.report[suffix]
                    stats.update(self.server.report[None])
                    timestamp = int(stats['time'] * 1000)
                    del(stats['time'])
                    collect_agent.send_stat(timestamp, suffix=suffix, **stats)
            self.server.report = None
        # Just another line under the sunshine
        elif self.server.report and msg.startswith('Proto Info:'):
            load(msg)


    def finish(self):
        pass


def connect_to_collect_agent():
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/norm/norm_rstats_filter.conf')
    if not success:
        collect_agent.send_log(syslog.LOG_ERR, "Error connecting to collect-agent")
        sys.exit(1)

    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job NORM')

def send_mode(address, port, iface, directory, max_rate, first_segment, last_segment, pipe):
    collect_agent.send_log(
            syslog.LOG_DEBUG,
            'NORM will send {} from segment '
            'number {}'.format(address, first_segment))

    instance = pynorm.Instance()
    instance.openDebugPipe(pipe)
    instance.setDebugLevel(3)
    session = instance.createSession(address, port)
    session.setReportInterval(1)
    session.setMulticastInterface(iface)
    session.setCongestionControl(True, True)
    session.setTxRateBounds(10000, max_rate)
    session.startSender(randint(0, 1000), 1024**2, 1400, 64, 16)

    number_pattern = re.compile(r'2s([0-9]+)\.m4s$')
    files_found = set()
    while True:
        for root, dirs, files in os.walk(os.path.expanduser(directory), topdown=True):
            for filename in files:
                filepath = os.path.join(root, filename)
                file_name = filepath[len(directory):].lstrip('/')
                number_groups = number_pattern.search(filename)
                if number_groups is None:
                    _, extension = os.path.splitext(filename)
                    if extension == '.mpd':
                        files_found.add(Element(-1, filepath, file_name))
                    elif extension == '.mp4':
                        files_found.add(Element(0, filepath, file_name))
                else:
                    file_number = int(number_groups.group(1))
                    if last_segment is None or file_number <= last_segment:
                        files_found.add(Element(file_number, filepath, file_name))

        first_element = Element(first_segment, None, None)
        if first_element not in files_found:
            time.sleep(1)
            continue

        for element in sorted(filter(first_element.__le__, files_found)):
            if element.sent:
                first_segment += 1
                continue
            if element.file_number != first_segment:
                break

            collect_agent.send_log(
                    syslog.LOG_DEBUG,
                    'NORM to {}: Sending file: {}'
                    .format(address, element.filename))
            session.fileEnqueue(element.filepath, element.filename)
            element.sent = True

            first_segment += 1

            for event in instance:
                if str(event) in END_OF_TRANSMISSION_EVENTS:
                    break


def receive_mode(address, port, iface, directory, pipe):
    os.nice(-10)
    path = os.path.abspath(os.path.expanduser(directory))
    instance = pynorm.Instance()
    instance.openDebugPipe(pipe)
    instance.setDebugLevel(3)
    instance.setCacheDirectory(path)
    session = instance.createSession(address, port)
    session.setReportInterval(1)
    session.setMulticastInterface(iface)
    session.startReceiver(1024 * 1024)

    for event in instance:
        if event == 'NORM_RX_OBJECT_INFO':
            filename = event.object.info.decode()
            event.object.filename = os.path.join(path, filename)
            collect_agent.send_log(
                    syslog.LOG_DEBUG,
                    'Receiving file {}'.format(event.object.filename))

        elif event == 'NORM_RX_OBJECT_COMPLETED':
            os.chmod(event.object.filename, 0o644)
            collect_agent.send_log(
                    syslog.LOG_DEBUG,
                    'File {} completed'.format(event.object.filename))

        elif event == 'NORM_RX_OBJECT_ABORTED':
            collect_agent.send_log(
                    syslog.LOG_DEBUG,
                    'File {} aborted'.format(event.object.filename))

def main(args):
    connect_to_collect_agent()
    with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as tempfn:
        pass
    server = CustomUnixDatagramServer(tempfn.name, UDPUnixRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    try:
        if args.mode == 'tx':
            send_mode(
                    args.address, args.port, args.iface,
                    args.directory, args.max_rate,
                    args.first_seg, args.last_seg, tempfn.name)
        else:
            receive_mode(
                    args.address, args.port, args.iface,
                    args.directory, tempfn.name)
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            'iface', help='The interface to transmit multicast on.')
    parser.add_argument(
            'directory', help='Directory list to transmit.')
    subparsers = parser.add_subparsers(
            dest='mode', metavar='mode',
            help='the mode to operate')
    subparsers.required = True

    parser_rx = subparsers.add_parser('rx', help='operate on mode reception')
    parser_rx.add_argument(
            '-a', '--address', default='224.1.2.3',
            help='The IP address to bind to')
    parser_rx.add_argument(
            '-p', '--port', type=int, default=6003,
            help='The port number to listen on')

    parser_tx = subparsers.add_parser(
            'tx', help='operate on mode transmission')
    parser_tx.add_argument(
            '-a', '--address', default='224.1.2.3',
            help='The IP address to bind to')
    parser_tx.add_argument(
            '-p', '--port', type=int, default=6003,
            help='The port number to listen on')
    parser_tx.add_argument(
            '-m', '--max-rate', type=int, required=True,
            help='Maximal rate in bytes.')
    parser_tx.add_argument(
            '-f', '--first-seg', type=int, default=-1,
            help='First segment number to send.')
    parser_tx.add_argument(
            '-l', '--last-seg', type=int,
            help='Last segment number to send.')

    args = parser.parse_args()
    main(args)
