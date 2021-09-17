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


"""Sources of the Job chat_simu_srv"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Léa THIBOUT <lea.thibout@viveris.fr>
'''

import os
import sys
import time
import signal
import socket
import syslog
import select
import argparse
import traceback
import contextlib
from functools import partial

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


def tcp_pong(sock, message_number):
    message = sock.recv(1024)
    collect_agent.send_stat(now(), bytes_received=len(message))
    if not message:
        return False

    response = f"I’m the server -> client msg number {message_number}".encode()
    sock.send(response)
    collect_agent.send_stat(now(), bytes_sent=len(response))
    return True


def close_connections(clients, signum, frame):
    for sock in clients:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
    clients.clear()


def main(server_ip, server_port, keep_alive):
    start = time.perf_counter()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind((server_ip, server_port))

    s.listen(5)
    clients = {}

    if keep_alive:
        clients[s] = 0
    else:
        client, _ = s.accept()
        clients[client] = 0

    handler = partial(close_connections, clients)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    
    with contextlib.closing(s):
        while clients:
            incomming, _, _ = select.select(clients, [], [], 0.1)
            for sock in incomming:
                if sock is s:
                    client, _ = sock.accept()
                    clients[client] = 0
                else:
                    clients[sock] += 1
                    alive = tcp_pong(sock, clients[sock])
                    if not alive:
                        del clients[sock]
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()
        s.shutdown(socket.SHUT_RDWR)
    
    duration = time.perf_counter() - start
    collect_agent.send_stat(int(time.time() * 1000), duration=duration)


if __name__ == '__main__':
    with use_configuration('/opt/openbach/agent/jobs/chat_simu_srv/chat_simu_srv_rstats_filter.conf'):
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('server_ip', type=str, metavar='server_ip',
                    help='The host address IP of the traffic')
        parser.add_argument('server_port', type=int, metavar='server_port',
                    help='The host port of the traffic')
        parser.add_argument('-e', '--exit', action='store_true',
                    help='Exit as soon as there is no more clients connected'
                    ' instead of keeping the socket alive for further connections')

        args = parser.parse_args()

        main(args.server_ip, args.server_port, not args.exit)
