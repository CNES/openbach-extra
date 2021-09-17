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


"""Sources of the Job chat_simu_clt"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Léa THIBOUT <lea.thibout@viveris.fr>
'''

import os
import sys
import time
import socket
import syslog
import argparse
import traceback
import contextlib

import collect_agent


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


def now():
    return int(time.time() * 1000)


def tcp_ping(sock, message_number):
    message = f"I’m the client -> server msg number {message_number}".encode()
    sock.send(messages)
    collect_agent.send_stat(now(), bytes_sent=len(message))
    response = sock.recv(1024)
    collect_agent.send_stat(now(), bytes_received=len(response))


def main(server_ip, server_port, nb_msg):
    start = time.perf_counter()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))

    with contextlib.closing(s):
        for i in range(nb_messages):
            tcp_ping(s, i + 1)
        s.shutdown(socket.SHUT_RDWR)
    
    duration = time.perf_counter() - start
    collect_agent.send_stat(now(), duration=duration)


if __name__ == "__main__":
    with use_configuration('/opt/openbach/agent/jobs/chat_simu_clt/chat_simu_clt_rstats_filter.conf'):
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('server_ip', type=str, metavar='server_ip',
                    help='The host address IP of the traffic')
        parser.add_argument('server_port', type=int, metavar='server_port',
                    help='The host port of the traffic')
        parser.add_argument('-m', '--msg', type=int, metavar='msg', default=3, help='The number of messsages sent')

        # get args
        args = parser.parse_args()
        server_ip = args.server_ip
        server_port = args.server_port
        nb_msg = args.msg

        main(server_ip, server_port, nb_msg)
