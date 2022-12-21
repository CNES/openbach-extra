#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.

"""Sources of the voip_qoe_dest OpenBACH job"""

__author__ = 'Antoine AUGER'
__credits__ = '''Contributors:
 * Antoine AUGER <antoine.auger@tesa.prd.fr>
 * Bastien TAURAN <bastien.tauran@viveris.fr>
'''

import os
import sys
import time
import shutil
import socket
import syslog
import select
import argparse
import ipaddress
import threading
import subprocess
from pathlib import Path

import collect_agent


job_dir = Path('/opt/openbach/agent/jobs/voip_qoe_dest')

FINISHED = threading.Event()


def build_parser():
    """Method used to validate the parameters supplied to the program

    :return: an object containing required/optional arguments with their values
    :rtype: object
    """
    parser = argparse.ArgumentParser(
            description='Start a receiver (destination) component to measure QoE of one '
            'or many VoIP sessions generated with D-ITG software',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            'dest_addr', type=ipaddress.ip_address,
            help='The destination IPv4 address to use for the signaling channel')
    parser.add_argument(
            '-sp', '--signaling-port',
            type=int, default=9000,
            help='Signaling channel port number. Default: 9000.')
    parser.add_argument(
            '-cp', '--control-port',
            type=int, default=50000,
            help='The port used on the sender side to receive OpenBACH commands from '
            'the client. Should be the same on the sending side. Default: 50000.')

    return parser


def socket_thread(address, port):
    with socket.socket() as s:
        s.bind((address, port))
        s.listen(1)
        print('Server listening.... on', address, port)

        while not FINISHED.is_set():
            readable, _, _ = select.select([s], [], [], 1)
            if not readable:
                continue

            control_socket, addr = s.accept()
            print('Got connection from', addr)
            run = job_dir / 'logs' / 'run'

            with control_socket:
                while not FINISHED.is_set():
                    for _ in range(20):
                        readable, _, _ = select.select([control_socket], [], [], 1)
                        if readable:
                            break
                        if FINISHED.is_set():
                            return
                    else:
                        print('No message received in the last 20 seconds, exiting this run...')
                        break

                    command = control_socket.recv(1024).decode()
                    print('Received command:', command)

                    if command == 'BYE':
                        control_socket.shutdown(socket.SHUT_RDWR)
                        break
                    elif command == 'GET_LOG_FILE':
                        with run.joinpath('recv.log').open('rb') as f:
                            while True:
                                block = f.read(1024)
                                if not block:
                                    break
                                control_socket.send(block)
                        time.sleep(3)
                        print('TRANSFERT_FINISHED')
                        control_socket.send(b'TRANSFERT_FINISHED')
                    elif command == 'DELETE_FOLDER':
                        shutil.rmtree(run)
                    elif command.startswith('RUN_ID'):
                        run_id = command.split('-')[1]
                        print('run_id', run_id)
                        run = run.with_name('run' + run_id)
                        run.mkdir(parents=True, exist_ok=True)


def main(dest_addr, signaling_port, control_port):
    """Main method

    :return: nothing
    """
    try:
        th = threading.Thread(target=socket_thread, args=(str(args.dest_addr), args.control_port))
        th.start()
        try:
            process = subprocess.Popen(
                    ['ITGRecv', '-Sp', str(args.signaling_port)],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as ex:
            message = 'Error running ITGRecv : {}'.format(ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)

        while process.poll() is None:
            output = process.stdout.readline().strip()
            if output and output != 'Press Ctrl-C to terminate':
                collect_agent.send_log(syslog.LOG_DEBUG, output)
            print(output)

        msg = 'ITGRecv has exited with the following return code: {}'.format(output)  # Output contains return code
        collect_agent.send_log(syslog.LOG_DEBUG, msg)
    finally:
        FINISHED.set()
        th.join()


if __name__ == '__main__':
    with collect_agent.use_configuration(job_dir.joinpath('voip_qoe_dest_rstats_filter.conf').as_posix()):
        # Argument parsing
        args = build_parser().parse_args()
        main(**vars(args))
