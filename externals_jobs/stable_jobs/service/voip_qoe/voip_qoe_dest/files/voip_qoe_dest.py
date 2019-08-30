#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2018 CNES
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
 * Bastien TAURAN <bastien.tauran@toulouse.viveris.com>
'''

import argparse
import os
import ipaddress
import subprocess
import syslog
import collect_agent
import socket
import shutil
import time
import threading

job_name = "voip_qoe_dest"
common_prefix = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))  # /opt/openbach/agent/jobs


def build_parser():
    """
    Method used to validate the parameters supplied to the program

    :return: an object containing required/optional arguments with their values
    :rtype: object
    """
    parser = argparse.ArgumentParser(description='Start a receiver (destination) component to measure QoE of one or '
                                                 'many VoIP sessions generated with D-ITG software',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('dest_addr', type=ipaddress.ip_address, help='The destination IPv4 address to use for the '
                                                                     'signaling channel')
    parser.add_argument('-cp', '--control_port', type=int, default=50000,
                        help='The port used on the sender side to send and receive OpenBACH commands from the client.'
                             'Should be the same on the destination side.  Default: 50000.')
    return parser

def socket_thread(address, port):
    s = socket.socket()
    host = address
    try:
        s.bind((host, port))
    except socket.error as msg:
        print("Socket binding error: " + str(msg) + "\n" + "Retrying...")
    s.listen(1)

    print('Server listening.... on',host,port)


    while True:
        conn, addr = s.accept()
        print('Got connection from', addr)
        run_id = -1

        while True:
            command = conn.recv(1024).decode()
            print("Received command:", command)
            if command == "BYE":
                break
            elif command == "GET_LOG_FILE":
                f = open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs', 'run{}'.format(run_id), 'recv.log'),'rb')
                l = f.read(1024)
                while (l):
                   conn.send(l)
                   l = f.read(1024)
                f.close()
                time.sleep(5)
                print("TRANSFERT_FINISHED".encode())
                conn.send("TRANSFERT_FINISHED".encode())
            elif command == "DELETE_FOLDER":
                shutil.rmtree(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs', 'run{}'.format(run_id)))
            elif "RUN_ID" in command:
                run_id = int(command.split("-")[1])
                print("run_id",run_id)
                os.mkdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs', 'run{}'.format(run_id)))

        conn.close()


def main(args):
    """
    Main method

    :return: nothing
    """
    success = collect_agent.register_collect(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                          '{}_rstats_filter.conf'.format(job_name)))
    if not success:
        message = 'Could not connect to rstats'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)

    try:
        th = threading.Thread(target=socket_thread, args=(str(args.dest_addr),args.control_port))
        th.daemon = True
        th.start()
    except (KeyboardInterrupt, SystemExit):
        cleanup_stop_thread()
        exit()

    process = subprocess.Popen([os.path.join(common_prefix, job_name, 'D-ITG-2.8.1-r1023', 'bin', 'ITGRecv')],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        output = process.stdout.readline().decode().strip()
        if not output:
            if process.poll is not None:
                break
            continue
        if output != "Press Ctrl-C to terminate":
            collect_agent.send_log(syslog.LOG_DEBUG, output)
        print(output)

    msg = "ITGRecv has exited with the following return code: {}".format(output)  # Output contains return code
    collect_agent.send_log(syslog.LOG_DEBUG, msg)


if __name__ == "__main__":
    # No internal configuration needed for receiver side
    # Argument parsing
    args = build_parser().parse_args()
    main(args)
