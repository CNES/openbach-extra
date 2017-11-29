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
import time
import syslog
import argparse
from random import randint
from functools import total_ordering

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


def connect_to_collect_agent():
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/norm/norm_rstats_filter.conf')

    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job NORM')


def send_mode(address, port, iface, directory, max_rate, first_segment, last_segment):
    connect_to_collect_agent()

    collect_agent.send_log(
            syslog.LOG_DEBUG,
            'NORM will send {} from segment '
            'number {}'.format(address, first_segment))

    instance = pynorm.Instance()
    session = instance.createSession(address, port)
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

        first_element = Element(first_segment)
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
                if event in END_OF_TRANSMISSION_EVENTS:
                    break


def receive_mode(address, port, iface, directory):
    connect_to_collect_agent()

    os.nice(-10)
    path = os.path.abspath(os.path.expanduser(directory))
    instance = pynorm.Instance()
    instance.setCacheDirectory(path)
    session = instance.createSession(address, port)
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
    if args.mode == 'tx':
        send_mode(
                args.address, args.port, args.iface,
                args.directory, args.max_rate,
                args.first_seg, args.last_seg)
    else:
        receive_mode(args.address, args.port, args.iface, args.directory)
