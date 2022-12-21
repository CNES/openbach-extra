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


"""Sources of the Job outoforder_detect"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David FERNANDES <david.fernandes@viveris.fr>
'''


import sys
import time
import signal
import syslog
import socket
import argparse
import threading
from queue import Queue
from functools import partial

import collect_agent


def _parse_to_packets(entry):
    if entry.isnumeric():
        return int(entry)
    value, unit = int(entry[:-1]), entry[-1]
    if unit == 'K':
        return value * 1000
    if unit == 'M':
        return value * 1000 * 1000
    if unit == 'G':
        return value * 1000 * 1000 * 1000


def signal_term_handler(entity, sock, signal, frame):
    if entity == 'client': sock.sendall(b'stop_server')
    sock.close()
    message = 'Stoped job outoforder_detect.'
    collect_agent.send_log(syslog.LOG_DEBUG, message)
    sys.exit(message)


def timer(duration, q):
    time.sleep(duration)
    q.put('stop_transmitting')


def client(server_ip, server_port, signal_port, duration, transmitted_packets):
    # Set signalisation communication to the Server
    signal_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        signal_socket.connect((server_ip, signal_port))
    except ConnectionRefusedError:
        message = 'Error : Cannot connect to server'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Manage SIGTERM and SIGINT signals behavior
    signal.signal(signal.SIGTERM, partial(signal_term_handler, 'client', signal_socket))
    signal.signal(signal.SIGINT, partial(signal_term_handler, 'client', signal_socket))

    if duration:
        q = Queue()
        t_timer = threading.Thread(target=timer, args=(duration, q))
        t_timer.daemon = True
        t_timer.start()

    id = 0
    while True:
        if ((transmitted_packets is not None and id == _parse_to_packets(transmitted_packets))
                or (duration and not q.empty())):
            time.sleep(1) # Wait that all the UDP packets are sent to prevent deordering of the TCP message
            signal_socket.sendall(b'stop_server')
            data = signal_socket.recv(1024)
            signal_socket.close()
            break
        client_socket.sendto(str(id).encode(), (server_ip, server_port))
        id = id + 1


def signalisation(address, port, q, exit):
    # Launch TCP Server for signalisation
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as signal_socket:
        signal_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        signal_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        signal_socket.bind((address, port))
        signal_socket.listen()
        while True:
            connect, addr = signal_socket.accept()
            with connect:
                message = 'Server got connection from client {} '.format(addr)
                collect_agent.send_log(syslog.LOG_DEBUG, message)
                print(message)
                data = connect.recv(1024)
                if data.decode() == 'stop_server':
                    if exit:
                        # Send message to main thread : stop the server
                        q.put('stop_server')
                        break
                    else:
                        # Send message to main thread : reinitialize the server
                        q.put('reinit_server')
                else:
                    message = 'Warning : Unknown message comming from the Client: {}'.format(data)
                    collect_agent.send_log(syslog.LOG_WARNING, message)
                    print(message)


def parse_udp(server_socket, q_signal):
    received = [] # Received UDP packets
    in_order = [] # In order packets
    out_of_order = [] # Out of order packets
    server_socket.settimeout(None)
    prev_id, _ = server_socket.recvfrom(1024)
    received.append(int(prev_id))
    server_socket.settimeout(1)
    while q_signal.empty():
        try:
            new_id, _ = server_socket.recvfrom(1024)
        except socket.timeout:
            continue
        else:
            received.append(int(new_id))

    total_received = len(received)
    in_order.append(received.pop(0))

    while received:
        if received[0] < in_order[-1]:
            out_of_order.append(received.pop(0))
        else:
            in_order.append(received.pop(0))

    ooo = len(out_of_order),
    dupes = len(received) - len(set(received))
    collect_agent.send_stat(
            collect_agent.now(),
            total_packets_received=total_received,
            out_of_order_packets=ooo,
            out_of_order_ratio=ooo / total_received,
            duplicated_packets=dupes,
            duplicated_ratio=dupes / total_received,
    )
    message = q_signal.get_nowait()
    if message == 'stop_server':
        return True
    elif message == 'reinit_server':
        return None
    else:
        log = 'Unknown internal message : {}'.format(message)
        collect_agent.send_log(syslog.LOG_ERR, log)
        sys.exit(log)


def server(address, server_port, signal_port, exit):
    # Start TCP socket for signalisation
    q_signal = Queue()
    t_signal = threading.Thread(target=signalisation, args=(address, signal_port, q_signal, exit))
    t_signal.daemon = True
    t_signal.start()

    # Initialize UDP socket to receive data
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server_socket.bind((address, server_port))
    except Exception as ex:
        message = 'ERROR : Cannot bind socket at address {}:{}. {}.'.format(address, server_port, ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    # Manage SIGTERM and SIGINT signals
    signal.signal(signal.SIGTERM, partial(signal_term_handler, 'server', server_socket))
    signal.signal(signal.SIGINT, partial(signal_term_handler, 'server',  server_socket))

    # Parse UDP packets coming from the client
    stop_server = None
    while not stop_server:
        stop_server = parse_udp(server_socket, q_signal)


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/outoforder_detect/outoforder_detect_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
                '-p', '--server-port', type=int, default=61234,
                help='Set server port to receive UDP packets from de client')
        parser.add_argument(
                '-s', '--signal-port', type=int, default=61235,
                help='Set signalisation port to manage connection between client and server')
        # Sub-commands functionnality to split server and client mode
        subparsers = parser.add_subparsers(
                title='Subcommand mode',
                help='Choose the mode (server mode or client mode)')
        subparsers.required=True
        # Only server parameters
        parser_server = subparsers.add_parser('server', help='Run in server mode')
        parser_server.add_argument(
                '-e', '--exit', action='store_true',
                help='Exit upon completion of one connection.')
        parser_server.add_argument(
                '-a', '--address', type=str, default='0.0.0.0',
                help='The address to bind the server (default = 0.0.0.0)')
        # Only client parameters
        parser_client = subparsers.add_parser('client', help='Run in client mode')
        parser_client.add_argument(
                'server_ip', type=str,
                help='The IP address of the server')
        parser_client.add_argument(
                '-d', '--duration', type=float, default=5,
                help='The duration of the transmission in seconds. Set 0 to infinite test. (default = 5)')
        parser_client.add_argument(
                '-n', '--transmitted-packets', type=str,
                help='The number of packets to transmit. It has same priority as duration parameter. You can '
                'use [K/M/G]: set 100K to send 100.000 packets. (default = None)')

        # Set subparsers options to automatically call the right
        # function depending on the chosen subcommand
        parser_server.set_defaults(function=server)
        parser_client.set_defaults(function=client)

        # Get args and call the appropriate function
        args = vars(parser.parse_args())
        main = args.pop('function')
        main(**args)

