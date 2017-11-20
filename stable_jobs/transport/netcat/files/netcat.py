#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016 CNES
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


"""Sources of the Job netcat"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''

import sys
import time
import syslog
import argparse
import subprocess
from functools import partial

import collect_agent


def main(mode, port, persist, measure_t, filename, n_times):
    # Connect to collect agent
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/netcat/'
            'netcat_rstats_filter.conf')
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    collect_agent.send_log(syslog.LOG_DEBUG, "Starting job netcat")

    cmd = ['nc', mode, str(port)]
    if persist:
        cmd.insert(1, '-k')
    if measure_t:
        cmd = ['/usr/bin/time', '-f', '%e', '--quiet'] + cmd

    process = partial(
            subprocess.run, cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE)
    for _ in range(n_times):
        try:
            if filename:
                with open(filename) as file_in:
                    p = process(stdin=file_in)
            else:
                p = process()
        except Exception as ex:
            collect_agent.send_log(
                    syslog.LOG_ERR,
                    'ERROR executing netcat: {}'.format(ex))
            continue

        if measure_t and p.returncode == 0:
            timestamp = int(time.time() * 1000)
            stderr = p.stderr
            try:
                duration = float(stderr)
            except ValueError:
                collect_agent.send_log(
                        syslog.LOG_ERR,
                        'ERROR: cannot convert output to '
                        'duration value: {}'.format(stderr))
            else:
                try:
                    collect_agent.send_stat(timestamp, duration=duration)
                except Exception as ex:
                    collect_agent.send_log(
                            syslog.LOG_ERR,
                            'ERROR sending stat: {}'.format(ex))
        elif p.returncode:
            collect_agent.send_log(
                    syslog.LOG_ERR,
                    'ERROR: return code {}: {}'.format(p.returncode, p.stderr))


if __name__ == '__main__':
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
            '-l', '--listen', action='store_true',
            help='Run in server mode')
    group.add_argument(
            '-c', '--client', type=str,
            help='Run in client mode (specify remote IP address)')
    parser.add_argument(
            '-p', '--port', type=int, default=5000,
            help='The port number')
    parser.add_argument(
            '-k', '--persist', action='store_true',
            help='Keep listening after current connection is completed')
    parser.add_argument(
            '-t', '--time', action='store_true',
            help='Measure the duration of the process')
    parser.add_argument(
            '-n', '--n-times', type=int, default=1,
            help='The number of times the connection is established')
    parser.add_argument(
            '-f', '--file', type=str,
            help='The path of a file to send to the server')

    # get args
    args = parser.parse_args()
    server = args.listen
    client = args.client
    n_times = args.n_times
    port = args.port
    mode = '-l' if server else client
    persist = args.persist
    measure_t = args.time
    filename = args.file

    main(mode, port, persist, measure_t, filename, n_times)
