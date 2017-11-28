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
'''

import re
import sys
import time
import psutil
import syslog
import os.path
import argparse
import subprocess
from random import randint
from contextlib import suppress

import pynorm
import collect_agent

class Element:
    """
        An element is defined by :
        - The file name (the filename is the segment number)
        - A flag which indicates if it has been sent or not
    """

    def __init__(self, filename, sent):
        self.filename = filename
        self.sent = sent

    def _get_file_name(self):
        return self.filename

    def _get_sent_flag(self):
        return self.sent

    def _set_file_name(self, filename):
        self.filename = filename

    def _set_sent_flag(self, sent):
        self.sent = sent

    def __lt__(self, other):
        if hasattr(other, 'filename'):
            return self.filename < other.filename
        return False

    def __eq__(self, other):
        if hasattr(other, 'filename'):
            return self.filename == other.filename
        return False


def main(mode=None, directory=None, iface=None, address=None,
        port=None, name=None, max_rate=None, first_seg=None):
    # Connect to the collect-agent
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/norm/norm_rstats_filter.conf')

    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job NORM')

    if (mode == 'tx'):
        if first_seg is None:
            first_seg = 1

        collect_agent.send_log(syslog.LOG_DEBUG,
                'NORM will send {} from segment number {}'.format(address, first_seg))

        instance = pynorm.Instance()
        session = instance.createSession(address, port)
        if iface:
            session.setMulticastInterface(iface)

        session.setCongestionControl(True,True)
        session.setTxRateBounds(10000, max_rate)
        session.startSender(randint(0, 1000), 1024**2, 1400, 64, 16)

        ordered_list = list()
        while True:
            news = False
            for root, dirs, files in os.walk(directory, topdown=True):
                if len(files)<5:  
                    time.sleep(1)
                    break

                for filename in files:
                    with suppress(AttributeError):
                        file_number = int(re.search('2s[0-9]+', filename).group(0)[2:])
                        if (file_number < first_seg):
                            continue
                        if not any({ 
                                elem.filename == file_number
                                for elem in ordered_list }):
                            ordered_list.append(Element(file_number, False))
                            news = True
            if not news:
                continue

            ordered_list.sort()

            for elt in ordered_list:
                if elt.sent == True:
                    continue
                collect_agent.send_log(syslog.LOG_DEBUG,
                        'NORM to {}: Sending segment number {}'.format(address, elt.filename))
                session.fileEnqueue(
                        '{}{}_2s{}.m4s'.format(directory, name, elt.filename),
                        '{}_2s{}.m4s'.format(name, elt.filename))
                elt.sent = True

                try:
                    for event in instance:
                        if event == 'NORM_TX_QUEUE_EMPTY':
                            break
                        elif event == 'NORM_TX_FLUSH_COMPLETED':
                            break
                        else:
                            pass
                except KeyboardInterrupt:
                    return 0

    elif (mode == 'rx'):
        prio = psutil.Process(os.getpid())
        prio.nice(-10)
        path = os.path.abspath(directory)
        instance = pynorm.Instance()
        instance.setCacheDirectory(path)
        session = instance.createSession(address, port)
        if iface:
            session.setMulticastInterface(iface)
        session.startReceiver(1024*1024)

        with suppress(KeyboardInterrupt):
            for event in instance:
                if event == 'NORM_RX_OBJECT_INFO':
                    event.object.filename = os.path.join(path, event.object.info.decode())
                    collect_agent.send_log(syslog.LOG_DEBUG,
                            'Receiving file {}'.format(event.object.filename))

                elif event == 'NORM_RX_OBJECT_COMPLETED':
                    cmd = ['chmod', '644', event.object.filename]
                    subprocess.run(cmd)
                    collect_agent.send_log(syslog.LOG_DEBUG,
                            'File {} completed'.format(event.object.filename))

                elif event == 'NORM_RX_OBJECT_ABORTED':
                    collect_agent.send_log(syslog.LOG_DEBUG,
                            'File {} aborted'.format(event.object.filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-a', '--address', default='224.1.2.3',
                      help='The IP address to bind to')
    parser.add_argument('-p', '--port', type=int, default=6003,
                      help='The port number to listen on')
    subparsers = parser.add_subparsers(
            dest='mode', metavar='mode',
            help='the mode to operate')
    subparsers.required = True
    parser_rx = subparsers.add_parser(
            'rx', help='operate on mode reception')
    parser_rx.add_argument('iface', type=str,
                      help='The inteface to transmit multicast on.')
    parser_rx.add_argument('directory', type=str,
                      help='Directory list to transmit.')

    parser_tx = subparsers.add_parser(
            'tx', help='operate on mode transmission')
    parser_tx.add_argument('iface', type=str,
                      help='The inteface to transmit multicast on.')
    parser_tx.add_argument('directory', type=str,
                      help='Directory list to transmit.')
    parser_tx.add_argument('max_rate', type=int,
                      help='Maximal rate in bytes.')
    parser_tx.add_argument('name', type=str,
                      help='Name of the content without spaces. Ex: BigBuckBunny.')
    parser_tx.add_argument('-f', '--first-seg', type=int,
                      help='First segment number to send.')
    
    args = parser.parse_args()
    main(**vars(args))
