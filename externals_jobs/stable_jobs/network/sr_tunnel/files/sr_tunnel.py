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


"""Sources of the Job sr_tunnel"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David FERNANDES <david.fernandes@viveris.fr>
'''


import re
import sys
import time
import signal
import syslog
import argparse
import threading
import subprocess
from functools import partial

import collect_agent


"""
Collected metrics from the trace file :
    p : Packet received
    P : Packet transmitted
    A : ACK transmitted
    a : ACK received
    D : Dropped packet (due to generated losses)
    T : Packet retransmitted (due to generated losses)
"""

statistics = {
        'sent_packets': 0,
        'received_packets': 0,
        'sent_acks': 0,
        'received_acks': 0,
        'dropped_packets': 0,
        'retransmitted_packets': 0}
tokens_map = {
        'P': 'sent_packets',
        'p': 'received_packets',
        'A': 'sent_acks',
        'a': 'received_acks',
        'D': 'dropped_packets',
        'T': 'retransmitted_packets'}


def run_command(cmd):
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if p.returncode:
        message = "Error when executing command '{}': '{}'".format(
                    ' '.join(cmd), p.stderr.decode())
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    return p.returncode, p.stdout.decode()


def signal_term_handler(p, signal, frame):
    p.terminate()


def prepare_tunnel(tun_ip):
    cmds = [[] for i in range(0,3)]
    cmds[0] = ['ip', 'tuntap', 'add', 'mode', 'tun', 'tun0']
    cmds[1] = ['ip', 'link', 'set', 'tun0', 'up']
    cmds[2] = ['ip', 'addr', 'add', tun_ip, 'dev', 'tun0']
    for cmd in cmds:
        run_command(cmd)


def parse_line(line):
    pattern = r'([AaPpDT])\s(?:\d{1,3}\.){3}\d{1,3}:'
    token = re.findall(pattern, line)
    if token:
        statistics[tokens_map[token[0]]] += 1


def tail(filename, p):
    counter = 0
    with open(filename) as f:
        while True:
            data = f.readline()
            if data:
                yield data
                continue
            if p.poll() is not None: # Process has terminate
                if counter < 1:
                    counter += 0.1
                else:
                    break # 1 second elapsed since process termination
            time.sleep(0.1) 


def collect_metrics():
    while True:
        collect_agent.send_stat(collect_agent.now(), **statistics)
        time.sleep(1)


def main(mode, tun_ip=None, server_ip=None, server_port=None, drop=None, burst=None, trace=None):
    message = 'Starting sr_tunnel job in {} mode'.format(mode)
    collect_agent.send_log(syslog.LOG_DEBUG, message)
    print(message)
    prepare_tunnel(tun_ip)

    cmd = ['/opt/openbach/agent/jobs/sr_tunnel/sr_tunnel_src/bin/sr_tunnel']
    cmd += ['-i', 'tun0']
    if mode == 'client':
        cmd += ['-c', server_ip]
    if mode == 'server':
        cmd += ['-s']
    cmd += ['-t', trace]
    if server_port is not None:
        cmd += ['-p', str(server_port)]
    if drop is not None:
        cmd += ['-d', str(drop)]
    if burst is not None:
        cmd += ['-b', str(burst)]

    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    collect_t = threading.Thread(target=collect_metrics) 
    collect_t.daemon = True
    collect_t.start()

    time.sleep(1)

    # Manage SIGTERM and SIGINT signals
    signal.signal(signal.SIGTERM, partial(signal_term_handler, p))
    signal.signal(signal.SIGINT, partial(signal_term_handler, p))

    for line in tail(trace, p):
        parse_line(line)

    cmd = ['ip', 'link', 'delete', 'tun0']
    run_command(cmd)
    message = 'Stopped job sr_tunnel.'
    collect_agent.send_log(syslog.LOG_DEBUG, message)
    print(message)


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/sr_tunnel/sr_tunnel_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
                'tun_ip', type=str,
                help='IPv4/mask addres of the local "tun0" interface that will be created.')
        parser.add_argument(
                '-t', '--trace', type=str, default='/opt/openbach/agent/jobs/sr_tunnel/sr_tunnel.log',
                help='The path to store the trace of packets')
        parser.add_argument(
                '-d', '--drop', type=int,
                help='emulate link-layer losses by dropping sent packet (expressed in percentage of drop from 0 to 100)')
        parser.add_argument(
                '-b', '--burst', type=int,
                help='Average burst size. GE model for losses. Default is 1 if -d is set')

        # Sub-commands functionnality to split server and client mode
        subparsers = parser.add_subparsers(
                title='Subcommand mode',
                help='Choose the mode (server mode or client mode)')
        subparsers.required=True

        # Only SERVER parameters
        parser_server = subparsers.add_parser('server', help='Run in server mode')
        parser_server.add_argument(
                '-p', '--port', type=int, dest='server_port',
                help='Port to listen on (Default 30001)')

        # Only CLIENT parameters
        parser_client = subparsers.add_parser('client', help='Run in client mode')
        parser_client.add_argument(
                'server_ip', type=str,
                help='The IP address of the server ("physical" interface address, not "tun0"')
        parser_client.add_argument(
                '-p', '--server-port', type=int,
                help='Port of the server (Default 30001)')

        # Set subparsers options to automatically call the right
        # mode depending on the chosen subcommand
        parser_server.set_defaults(mode='server')
        parser_client.set_defaults(mode='client')

        # Get args and call the appropriate mode
        args = vars(parser.parse_args())
        main(**args)

