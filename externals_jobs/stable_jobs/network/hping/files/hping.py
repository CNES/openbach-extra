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


"""Sources of the Job hping"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David PRADAS <david.pradas@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
 * Bastien TAURAN <bastien.tauran@toulouse.viveris.com>
'''

import os
import sys
import time
import shlex
import syslog
import argparse
import traceback
import contextlib
from subprocess import Popen, PIPE, STDOUT
from statistics import mean

import collect_agent


def main(destination_ip, count, interval, microseconds, n_mean, destport):
    cmd = ['stdbuf', '-oL']
    cmd += ['hping3', str(destination_ip), '-S']
    if destport:
        cmd += ['-p', str(destport)]
    if count:
        cmd += ['-c', str(count)]
    if interval:
        if microseconds:
            cmd += ['-i', 'u'+str(interval)]
        else:
            cmd += ['-i', str(interval)]

    measurements = []

    # launch command
    p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
    while True:
        timestamp = collect_agent.now()
        rtt_data = None

        # read output
        output = p.stdout.readline().decode()
        if not output:
            if p.poll is not None:
                break
            continue

        try:
            for col in reversed(output.split()):
                if not col.startswith('rtt='):
                    continue
                rtt_data = float(col.split('=')[1])
                break
        except Exception as ex:
            message = 'ERROR: {}'.format(ex)
            collect_agent.send_stat(timestamp, status=message)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)

        if rtt_data is None:
            continue

        measurements.append(rtt_data)
        if len(measurements) == n_mean:
            collect_agent.send_stat(timestamp, rtt=mean(measurements))
            measurements = []


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/hping/hping_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
                'destination_ip', help='The destination the '
                'hping (IP address, hostname, domain name, etc.)')
        parser.add_argument(
                '-p', '--destport', type=int, default=443,
                help='Destination port for TCP SYN  (default=443, strongly '
                'recommended)')
        parser.add_argument(
                '-c', '--count', type=int, 
                help='Number of packets to send (default=unlimited).')
        parser.add_argument(
                '-i', '--interval', type=str,
                help='Interval, in seconds, between each packet sent (default=1). '
                'The interval can be set in micro seconds '
                'by adding u before the interval value (u40 for 40 micro seconds). '
                'The interval can be a float, '
                'with a minimum granularity of 1 micro second.', default=1)
        parser.add_argument(
                '-m', '--mean', type=int, 
                help='Collect the mean RTT of every N packets.', default=1)

        # get args
        args = parser.parse_args()
        destport = args.destport
        destination_ip = args.destination_ip
        count = args.count
        interval = str(args.interval)
        n_mean = args.mean

        try:
            if len(interval) > 0 and interval[0] == 'u':
                interval = int(float(interval[1:]))
                microseconds = True
            else:
                microseconds = False
                interval = float(interval)
                if interval != int(interval):
                    interval = int(interval*1000000)
                    microseconds = True
                else:
                    interval = int(interval)
        except ValueError:
            interval = 0
            microseconds = False

        main(destination_ip, count, interval, microseconds, n_mean, destport)
