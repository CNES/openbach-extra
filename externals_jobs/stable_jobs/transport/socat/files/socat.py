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


"""Sources of the Job netcat"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import re
import os
import sys
import time
import syslog
import pathlib
import argparse
import subprocess

import collect_agent


TMP_FILENAME = pathlib.Path('/tmp/socat.out')


def compact_bytes(value):
    match = re.fullmatch(r'(\d+)(K|M|G)?', value)
    if not match:
        raise argparse.ArgumentError('wrong format: use numbers followed by an optionnal K, M, or G')

    base, unit = match.groups()
    if unit == 'K':
        return int(base) * 1024
    elif unit == 'M':
        return int(base) * 1024 * 1024
    elif unit == 'G':
        return int(base) * 1024 * 1024 * 1024
    else:
        return int(base)


def server(port, send_file=None, create_file=None, measure_time=False):
    if send_file:
        with send_file:
            filename = send_file.name

    if create_file:
        filename = TMP_FILENAME.as_posix()
        output_file = 'of={}'.format(filename)
        file_size = 'count={}'.format(create_file)
        try:
            subprocess.run(['dd', 'if=/dev/zero', output_file, 'bs=1', file_size], check=True)
        except subprocess.CalledProcessError:
            message = 'WARNING wrong return code when creating file'
            collect_agent.send_log(syslog.LOG_WARNING, message)

    cmd = [
            'socat', 'TCP-LISTEN:{},reuseaddr,fork,crlf'.format(port),
            'SYSTEM:"cat {}"'.format(filename),
    ]
    p = _run_command(cmd, measure_time)
    TMP_FILENAME.unlink(missing_ok=True)

    if measure_time:
        _send_statistics(p)


def client(dest, port, expected_size=None, measure_time=False):
    cmd = ['socat', '-u', 'TCP:{}:{}'.format(dest, port), 'OPEN:{},creat,trunc'.format(TMP_FILENAME)]
    p = _run_command(cmd, measure_time)

    if expected_size and expected_size != TMP_FILENAME.lstat().st_size:
        message = 'Wrong file size: expecting {}, got {}'.format(expected_size, TMP_FILENAME.lstat().st_size)
        collect_agent.send_log(syslog.LOG_WARNING, message)
    TMP_FILENAME.unlink(missing_ok=True)

    if measure_time:
        _send_statistics(p)


def _run_command(cmd, measure_time):
    if measure_time:
        cmd = ['/usr/bin/time', '-f', '%e', '--quiet'] + cmd

    try:
        return subprocess.run(
                cmd, stdout=subprocess.DEVNULL,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True)
    except Exception as ex:
        message = "ERROR executing socat: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(mesage)


def _send_statistics(proccess):
    returncode = process.returncode
    output = process.stderr

    if returncode:
        message = 'ERROR: return code {}: {}'.format(returncode, output)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    try:
        duration = float(output)
    except ValueError:
        message = 'ERROR: cannot convert output to duration value: {}'.format(output)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    else:
        try:
            collect_agent.send_stat(collect_agent.now(), duration=duration)
        except Exception as ex:
            collect_agent.send_log(syslog.LOG_ERR, 'ERROR sending stat: {}'.format(ex))


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/socat/socat_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
                'port', type=int,
                help='The TCP port number')
        parser.add_argument(
                '-t', '--measure-time',
                action='store_true',
                help='Measure the duration of the process')

        subparsers = parser.add_subparsers(
            title='Subcommand mode',
            help='Choose the socat mode (server mode or client mode)')
        subparsers.required = True

        # Only server parameters
        parser_server = subparsers.add_parser('server', help='Run in server mode')
        group = parser_server.add_mutually_exclusive_group(required=True)
        group.add_argument(
                '-f', '--send-file',
                type=argparse.FileType('r'),
                help='The file to send back to clients upon connection')
        group.add_argument(
                '-c', '--create-file', type=compact_bytes,
                help='Generate a random file of the given size to send back to clients')

        # Only client parameters
        parser_client = subparser.add_parser('client', help='Run in client mode')
        parser_client.add_argument('dest', help='IP address of the server')
        parser_client.add_argument(
                '-e', '--expected-size', type=compact_bytes,
                help='The expected size of the file sent by the server. '
                'Will not check if not provided, will send an error if '
                'differences are found.')

        parser_server.set_defaults(function=server)
        parser_client.set_defaults(function=client)

        # Get args and call the appropriate function
        args = vars(parser.parse_args())
        main = args.pop('function')
        main(**args)
