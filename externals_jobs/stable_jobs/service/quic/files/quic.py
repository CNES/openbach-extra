#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2020 CNES
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


"""Sources of the Job quic"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Francklin SIMO <armelfrancklin.simotegueu@viveris.fr>
'''

import collect_agent
import syslog
import os
import sys
import argparse
import subprocess
import time
from enum import Enum
from ipaddress import ip_address
from pathlib import Path
import tempfile

DESCRIPTION = ("This job runs a client or a server QUIC. Supported QUIC implementations are: "
               "ngtcp2, picoquic, quicly. \n"
               "By default, each implementation is cloned from its standard repository. "
               "The installed version is the HEAD of the master branch. \n "
               "If you wish to install another version, you need to modify global variables "
               "related to the implementation to change. \n "
               "These variables are located at the begining of the install file of the job. "
               "So you have to change the address of the git repository as well as "
               "the version to install"
              )

SERVER_PORT = 4433
CERT = "/etc/ssl/certs/quic.openbach.com.crt"
KEY = "/etc/ssl/private/quic.openbach.com.pem"
HTDOCS = "/var/www/quic.openbach.com/"
DOWNLOAD_DIR = tempfile.mkdtemp(prefix='openbach_job_quic-')
LOG_DIR = tempfile.mkdtemp(dir=DOWNLOAD_DIR, prefix='logs-')


class Implementations(Enum):
    NGTCP2='ngtcp2'
    PICOQUIC='picoquic'
    QUICLY='quicly'


def connect_to_collect_agent():
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/quic/'
            'quic_rstats_filter.conf')
    if not success:
        message = 'Error connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


def now():
    return int(time.time() * 1000)


def run_command(cmd, cwd=None):
    "Run cmd and wait for command to complete then return a CompletedProcessess instance"
    try:
      p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=cwd, check=True)
    except Exception as ex:
        message = "Error running command '{}': '{}'".format(' '.join(cmd), ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)
    return p


def _command_build_helper(flag, value):
    if value is not None:
        yield flag
        yield str(value)


def build_cmd(implementation, mode, server_port, log_file, server_ip=None, resources=None, download_dir=None, extra_args=None):
    cmd = []
    _, server_port = _command_build_helper(None, server_port)
    if implementation == Implementations.NGTCP2.value:
       if mode == 'client':
          _, server_ip = _command_build_helper(None, server_ip)
          cmd.extend(['ngtcp2_client', server_ip, server_port])
          cmd.extend(['https://{}:{}/{}'.format(server_ip, server_port, res) for res in resources])
          cmd.extend(_command_build_helper('--download', download_dir))
          cmd.extend(['--exit-on-all-streams-close'])
          cmd.extend(_command_build_helper('--qlog-file', log_file))
          if extra_args: cmd.extend([extra_args])
       if mode == 'server':
          cmd.extend(['ngtcp2_server', '0.0.0.0', server_port])
          cmd.extend([KEY, CERT])
          cmd.extend(_command_build_helper('-d', HTDOCS))
          cmd.extend(_command_build_helper('--qlog-dir', os.path.split(log_file)[0]))
          if extra_args: cmd.extend([extra_args])
    if implementation == Implementations.PICOQUIC.value:
       cmd.extend(['picoquic'])
       if mode == 'client':
          _, server_ip = _command_build_helper(None, server_ip)
          cmd.extend(_command_build_helper('-o', download_dir))
          cmd.extend(_command_build_helper('-l', log_file))
          cmd.extend([server_ip, server_port])
          if extra_args: cmd.extend([extra_args])
          cmd.extend([';'.join(['/{}'.format(res) for res in resources])])
       if mode == 'server':
          cmd.extend(_command_build_helper('-c', CERT))
          cmd.extend(_command_build_helper('-k', KEY))
          cmd.extend(_command_build_helper('-w', HTDOCS))
          cmd.extend(_command_build_helper('-l', log_file))
          cmd.extend(_command_build_helper('-p', server_port))
          if extra_args: cmd.extend([extra_args])
    if implementation == Implementations.QUICLY.value:
       cmd.extend(['quicly'])
       if mode == 'client':
          _, server_ip = _command_build_helper(None, server_ip)
          _, server_port = _command_build_helper(None, server_port)
          cmd.extend(_command_build_helper('-e', log_file))
          cmd.extend(['-P /{}'.format(res) for res in resources])
          if extra_args: cmd.extend([extra_args])
          cmd.extend([server_ip, server_port])
       if mode == 'server':
          cmd.extend(_command_build_helper('-c', CERT))
          cmd.extend(_command_build_helper('-k', KEY))
          cmd.extend(_command_build_helper('-e', log_file))
          if extra_args: cmd.extend([extra_args])
          cmd.extend(['0.0.0.0', server_port])
    return cmd          


def client(implementation, server_port, log_dir, extra_args, server_ip, resources, download_dir, nb_runs):
    connect_to_collect_agent()
    for run_number in range(nb_runs):
        with open(os.path.join(log_dir, 'log_client_{}.txt'.format(str(run_number+1))), 'w+') as log_file:
             cmd = build_cmd(implementation, 'client', server_port, log_file.name, server_ip, [r for r in resources.split(',')], 
                             download_dir, extra_args=extra_args)
             start_time = now()
             p = run_command(cmd, cwd=download_dir)
             end_time = now()
             elapsed_time = end_time - start_time
             collect_agent.send_stat(now(), download_time=elapsed_time)

       
def server(implementation, server_port, log_dir, extra_args):
    connect_to_collect_agent()
    with open(os.path.join(log_dir, 'log_server.txt'), 'w+') as log_file:
         cmd = build_cmd(implementation, 'server', server_port, log_file.name, extra_args=extra_args)
         p = run_command(cmd, cwd=HTDOCS)


def writable_dir(path):
    ''' 
    Check if specified path is a path to an existing writable directory 
    Args:
        path: path to the directory to check
    Returns:
        abspath: absolute path to the directory to check
    Raises:
        ArgumentTypeError: if path does not exist 
                           if path does not a directory
                           if path does not a writable directory
    '''
    if (os.path.exists(path)):
        if not os.path.isdir(path):
            raise argparse.ArgumentTypeError("'{}' is not a path to a directory".format(path))
        if not os.access(path, os.W_OK):
           raise argparse.ArgumentTypeError("Directory is not writable: '{}'".format(path)) 
    else:
        raise argparse.ArgumentTypeError("Directory does not exist: '{}'".format(path))
    return path



if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(
               description=DESCRIPTION, 
               formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
               'implementation', 
               choices=[implem.value for implem in Implementations], 
               help='Choose a QUIC implementation. Know that, for each implementation ' 
                    'you can modify global variables to specify the address of the git repository '
                    'as well as the version to checkout',
    )
    
    parser.add_argument(
               '-p', '--server-port', type=int, default=SERVER_PORT,
               help='The server port to connect to/listen on' 
    )
    parser.add_argument(
               '-l', '--log-dir', type=writable_dir, default=LOG_DIR,
               help='The Path to the directory to save log files'
    ) 
    parser.add_argument(
               '-e', '--extra-args', type=str, default=None,
               help=('Allow to specify additional CLI arguments that are supported by chosen implementation. ' 
                     'From terminal, you need to run the name of the implementation follows by ' 
                      '\'-h\' to see specific supported arguments' 
                    )
    ) 
    # Sub-commands to split server and client mode
    subparsers = parser.add_subparsers(
               title='mode', help='Choose the running mode (server or client)'
    )
    parser_server = subparsers.add_parser(
               'server', 
               help='Run in server mode'
    )
    parser_client = subparsers.add_parser(
               'client', 
               help='Run in client mode'
    )
    parser_client.add_argument(
               'server_ip', type=ip_address, 
               help='The IP address of the server'
    )
    parser_client.add_argument(
               'resources', type=str, 
               help=('Comma-seprated list of resources to fetch in parallel over concurrent streams. '
                     'These resources must be located to the root of the directory \'{}\''.format(HTDOCS))
    )
    parser_client.add_argument(
               '-d', '--download-dir', type=writable_dir, default=DOWNLOAD_DIR, 
               help='The path to the directory  to save downloaded resources'
    )
    parser_client.add_argument(
               '-n', '--nb-runs', type=int, default=1,
               help='The number of times resources will be downloaded'
    )

    # Set subparsers options to automatically call the right
    # function depending on the chosen subcommand
    parser_server.set_defaults(function=server)
    parser_client.set_defaults(function=client)

    # Get args and call the appropriate function
    args = vars(parser.parse_args())
    main = args.pop('function')
    main(**args)


