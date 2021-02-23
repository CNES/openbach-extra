#!/usr/bin/env python3

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


"""Sources of the Job socket_stats_forwarder"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David FERNANDES <david.fernandes@viveris.fr>
'''

import os
import re
import sys
import time
import signal
import socket
import syslog
import argparse
import traceback
import contextlib
from functools import partial

import collect_agent

def signal_term_handler(udp_socket, signal, frame):
    message = 'Stoping job socket_stats_forwarder.'
    collect_agent.send_log(syslog.LOG_DEBUG, message)
    udp_socket.close()
    sys.exit(message)

@contextlib.contextmanager
def use_configuration(filepath):
    success = collect_agent.register_collect(filepath)
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job ' + os.environ.get('JOB_NAME', '!'))
    try:
        yield
    except Exception:
        message = traceback.format_exc()
        collect_agent.send_log(syslog.LOG_CRIT, message)
        raise
    except SystemExit as e:
        if e.code != 0:
            collect_agent.send_log(syslog.LOG_CRIT, 'Abrupt program termination: ' + str(e.code))
        raise

def main(args):
    # Bind UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_socket.bind((args.address, args.port))
    except OSError:
        message = 'ERROR : Cannot bind socket. Address already in use.'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    signal.signal(signal.SIGTERM, partial(signal_term_handler, udp_socket))
    signal.signal(signal.SIGINT, partial(signal_term_handler, udp_socket))

    # Receive and process data
    while True:
        data, _ = udp_socket.recvfrom(args.buffersize)
        for index, pair in enumerate(args.stats):
            match = re.search(pair[1], data.decode())
            if match:
                stats = dict()
                stats_names = pair[0].split(',')
                stats_values = match.groups()
                if len(stats_names) != len(stats_values):
                    message = 'ERROR : regular expression {} does not match with statistics names {}'.format(regexp, stats_names)
                    collect_agent.send_log(syslog.LOG_ERR, message)
                    sys.exit(message)
 
                for index, name in enumerate(stats_names):
                    stats[name] = float(stats_values[index])
                timestamp = int(time.time() * 1000)
                collect_agent.send_stat(timestamp, **stats)
                break

            if pair == args.stats[-1]:
                message = 'WARNING : no one regular expression match with data entry'
                collect_agent.send_log(syslog.LOG_WARNING, message)


if __name__ == "__main__":
    with use_configuration('/opt/openbach/agent/jobs/socket_stats_forwarder/socket_stats_forwarder_rstats_filter.conf'):
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            '-a', '--address', type=str, default='0.0.0.0',
            help='IP address to listen to')
        parser.add_argument(
            '-p', '--port', type=int, default=8321,
            help='Port number to listen to')
        parser.add_argument(
            '-b', '--buffersize', type=int, default=1024,
            help='Buffer size for data reception')
        parser.add_argument(
            '-s', '--stats', nargs=2, metavar=('NAMES', 'REGEXPS'), type=str,
            required=True, action='append',
            help='A comma-separated list of the stats names followed by the corresponding regexp')
    
        args = parser.parse_args()
        main(args)
