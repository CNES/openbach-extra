#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016−2019 CNES
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


"""Sources of the Job FTP Server"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Matthieu PETROU <matthieu.petrou@toulouse.viveris.com>

'''

import os
import syslog
import argparse
import time
import subprocess
import sys
import collect_agent

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer

failed_sent = 0
failed_received = 0


class MyHandler(FTPHandler):
    def on_file_received(self, file):
        timestamp = int(time.time() * 1000)        
        time_up = self.data_channel.get_elapsed_time()
        if time_up != 0:
                collect_agent.send_stat(timestamp,
                        throughput_received = self.data_channel.get_transmitted_bytes()*8/time_up)
                print(self.data_channel.get_transmitted_bytes()*8/time_up)

        os.system('rm -r /srv/' + file.split('/')[2])

    def on_file_sent(self, file):
        timestamp = int(time.time() * 1000)
        time_up = self.data_channel.get_elapsed_time()
        if time_up != 0:
                collect_agent.send_stat(timestamp, 
                        throughput_sent = self.data_channel.get_transmitted_bytes()*8/time_up)

    def on_incomplete_file_received(self, file):
        global failed_received
        timestamp = int(time.time() * 1000)
        failed_received += 1
        collect_agent.send_stat(timestamp, failed_file_received = failed_received)
        os.system('rm -r /srv/' + file.split('/')[2])

    def on_incomplete_file_sent(self, file):
        global failed_sent
        timestamp = int(time.time() * 1000)
        failed_sent += 1
        collect_agent.send_stat(timestamp, failed_file_sent = failed_sent)


def build_parser():
    parser = argparse.ArgumentParser(description='FTP Parser')
    parser.add_argument('server_ip', help = 'Server IP', type = str)
    parser.add_argument('port', help = 'Server port', type = int)
    parser.add_argument('--user', '-u', type = str, default = 'openbach',
        help = 'Authorized User (default openbach)')
    parser.add_argument('--password', '-p', type = str, default = 'openbach',
        help = "Authorized User's Password (default openbach)")
    parser.add_argument('--max_cons', type = int, default = 512,
        help = 'Limit of connexion on the server (default = 512)')
    parser.add_argument('--max_cons_ip', type = int, default = 0,
        help = 'Limit of connexion on the server per ip (default = 0 (unlimited))')

    return parser


def main(server_ip, port, user, password, max_cons, max_cons_ip,):
    config_file = '/opt/openbach/agent/jobs/ping/ping_rstats_filter.conf'
    success = collect_agent.register_collect(config_file)
    if not success:
        message = 'Could not connect to rstats'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)

    authorizer = DummyAuthorizer()
    authorizer.add_user(user, password, '/srv/', perm='elradfmwMT')

    handler = MyHandler
    handler.authorizer = authorizer

    address = (server_ip, port)
    server = ThreadedFTPServer(address, handler)

    server.max_cons = max_cons
    server.max_cons_per_ip = max_cons_ip


    server.serve_forever()


if __name__ == '__main__':
    args = build_parser().parse_args()
    main(args.server_ip, args.port, args.user, args.password, args.max_cons,
        args.max_cons_ip)

