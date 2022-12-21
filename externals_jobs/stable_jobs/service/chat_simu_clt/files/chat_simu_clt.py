#!/usr/bin/env python3

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


def tcp_ping(sock, message_number):
    message = f'I am the client -> server msg number {message_number}'.encode()
    sock.send(message)
    collect_agent.send_stat(collect_agent.now(), bytes_sent=len(message))
    print('Sent : {}'.format(message))
    response = sock.recv(1024)
    collect_agent.send_stat(collect_agent.now(), bytes_received=len(response))
    print('Received : {}'.format(response))



def main(server_ip, server_port, nb_msg):
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))
    start = time.perf_counter()

    with contextlib.closing(s):
        for i in range(nb_msg):
            tcp_ping(s, i + 1)
        s.shutdown(socket.SHUT_RDWR)
    
    duration = time.perf_counter() - start
    collect_agent.send_stat(collect_agent.now(), duration=duration)
    print('Duration of the test : {} s'.format(duration))


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/chat_simu_clt/chat_simu_clt_rstats_filter.conf'):
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
                'server_ip', type=str,
                help='The IP address of the server')
        parser.add_argument(
                '-p', '--server-port',
                type=int, default='55001',
                help='The port of the server')
        parser.add_argument(
                '-m', '--msg',
                type=int, default=3,
                help='The amount of messsages to send')

        # get args
        args = parser.parse_args()
        server_ip = args.server_ip
        server_port = args.server_port
        nb_msg = args.msg

        main(server_ip, server_port, nb_msg)
