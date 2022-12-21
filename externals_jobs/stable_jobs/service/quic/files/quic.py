#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


"""Sources of the Job quic"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Francklin SIMO <armelfrancklin.simotegueu@viveris.fr>
'''

import os
import sys
import string
import random
import shlex
import syslog
import argparse
import tempfile
import subprocess
from enum import Enum
from ipaddress import ip_address

import collect_agent


DESCRIPTION = (
        "This job runs a client or a server QUIC. Supported QUIC implementations are: "
        "ngtcp2, picoquic, quicly \n"
        "By default, for any implemenation, the installed version is the HEAD of the master branch. "
        "If you wish to install another version, you need to modify global variables related to the implementation "
        "at the begining of the install file of the job by speficying the address of the git repository as well as "
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
    # QUICLY='quicly'


class DownloadError(RuntimeError):
    def __init__(self, resource, p):
        self.message = (
                "Error downloading resource '{}'."
                "\n {} \n {}".format(resource, p.stdout.decode(), p.stderr.decode())
                )
        super().__init__(self.message)


def run_command(cmd, cwd=None):
    "Run cmd and wait for command to complete then return a CompletedProcessess instance"
    try:
        p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=cwd, check=False)
    except Exception as ex:
        message = "Error running command '{}': '{}'".format(' '.join(cmd), ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        print(message)
        sys.exit(message)
    return p


def _command_build_helper(flag, value):
    if value is not None:
        yield flag
        yield str(value)


def remove_resources(resources, download_dir):
    "Delete resources if already presents in *download_dir*"
    for r in resources.split(','):
        r_path = os.path.join(download_dir, r)
        if os.path.exists(r_path):
           os.remove(r_path)


def check_resources(resources, download_dir, p):
    "Check if resources have been successfully downloaded"
    downloaded_bytes = 0
    for r in resources.split(','):
        r_path = os.path.join(download_dir, r)
        if not os.path.exists(r_path) or os.path.getsize(r_path) <= 0:
            raise DownloadError(r, p)
        else:
            downloaded_bytes += os.path.getsize(r_path)

    return downloaded_bytes


def build_cmd(implementation, mode, server_port, store_logs, log_file, server_ip=None, resources=None, download_dir=None, extra_args=None):
    cmd = []
    _, server_port = _command_build_helper(None, server_port)
    if implementation == Implementations.NGTCP2.value:
        if mode == 'client':
            _, server_ip = _command_build_helper(None, server_ip)
            cmd.extend(['ngtcp2_client', server_ip, server_port])
            cmd.extend(['https://{}:{}/{}'.format(server_ip, server_port, res) for res in resources])
            cmd.extend(_command_build_helper('--download', download_dir))
            cmd.extend(['--exit-on-all-streams-close'])
            if store_logs: cmd.extend(_command_build_helper('--qlog-file', log_file))
            if extra_args: cmd.extend(shlex.split(extra_args))
        if mode == 'server':
            cmd.extend(['ngtcp2_server', '0.0.0.0', server_port])
            cmd.extend([KEY, CERT])
            cmd.extend(_command_build_helper('-d', HTDOCS))
            if store_logs: cmd.extend(_command_build_helper('--qlog-dir', os.path.split(log_file)[0]))
            if extra_args: cmd.extend(shlex.split(extra_args))
        cmd.extend(['-q'])
    if implementation == Implementations.PICOQUIC.value:
        cmd.extend(['picoquic'])
        if mode == 'client':
            sni = "".join(random.choice(string.ascii_letters) for i in range(10))
            _, server_ip = _command_build_helper(None, server_ip)
            cmd.extend(_command_build_helper('-n', sni))
            cmd.extend(_command_build_helper('-o', download_dir))
            if store_logs: cmd.extend(_command_build_helper('-l', log_file))
            if extra_args: cmd.extend(shlex.split(extra_args))
            cmd.extend([server_ip, server_port])
            cmd.extend([';'.join(['/{}'.format(res) for res in resources])])
        if mode == 'server':
            cmd.extend(_command_build_helper('-c', CERT))
            cmd.extend(_command_build_helper('-k', KEY))
            cmd.extend(_command_build_helper('-w', HTDOCS))
            if store_logs: cmd.extend(_command_build_helper('-l', log_file))
            cmd.extend(_command_build_helper('-p', server_port))
            if extra_args: cmd.extend(shlex.split(extra_args))
    if implementation == Implementations.QUICLY.value:
        cmd.extend(['quicly'])
        if mode == 'client':
            _, server_ip = _command_build_helper(None, server_ip)
            _, server_port = _command_build_helper(None, server_port)
            if store_logs: cmd.extend(_command_build_helper('-e', log_file))
            cmd.extend(['-p /{}'.format(res) for res in resources])
            if extra_args: cmd.extend(shlex.split(extra_args))
            cmd.extend([server_ip, server_port])
        if mode == 'server':
            cmd.extend(_command_build_helper('-c', CERT))
            cmd.extend(_command_build_helper('-k', KEY))
            if store_logs: cmd.extend(_command_build_helper('-e', log_file))
            if extra_args: cmd.extend(shlex.split(extra_args))
            cmd.extend(['0.0.0.0', server_port])
    return cmd          


def client(implementation, server_port, store_logs, log_dir, extra_args, server_ip, resources, download_dir, nb_runs):
    errors = []
    for run_number in range(nb_runs):
        with open(os.path.join(log_dir, 'log_client_{}.txt'.format(run_number + 1)), 'w+') as log_file:
            cmd = build_cmd(
                    implementation,
                    'client',
                    server_port,
                    store_logs,
                    log_file.name,
                    server_ip,
                    resources.split(','),
                    download_dir,
                    extra_args=extra_args)
            remove_resources(resources, download_dir) 
            start_time = collect_agent.now()
            p = run_command(cmd, cwd=download_dir)
            end_time = collect_agent.now()
        elapsed_time = end_time - start_time
        try:
            downloaded_bytes = check_resources(resources, download_dir, p)
        except DownloadError as error:
            errors.append((run_number + 1, error.message))
        else:
            collect_agent.send_stat(
                    collect_agent.now(),
                    download_time=elapsed_time,
                    downloaded_bytes=downloaded_bytes)

    if errors:
        message = '\n'.join('Error on run #{}: {}'.format(run, error) for run, error in errors)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

       
def server(implementation, server_port, store_logs, log_dir, extra_args):
    with open(os.path.join(log_dir, 'log_server.txt'), 'w+') as log_file:
         cmd = build_cmd(implementation, 'server', server_port, store_logs, log_file.name, extra_args=extra_args)
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
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/quic/quic_rstats_filter.conf'):
        # Argument parsing
        parser = argparse.ArgumentParser(
                   description=DESCRIPTION, 
                   formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        parser.add_argument(
                   'implementation', 
                   choices=[implem.value for implem in Implementations], 
                   help='Choose a QUIC implementation. Know that, for each implementation ' 
                        'you can modify global variables in install file to specify the address of the git repository '
                        'as well as the version to checkout',
        )
        
        parser.add_argument(
                   '-p', '--server-port', type=int, default=SERVER_PORT,
                   help='The server port to connect to/listen on' 
        )
        parser.add_argument(
                   '-s', '--store-logs', action='store_true',
                   help='Enable this option to store logs in the "log-dir" directory'
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
