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


"""Sources of the Job nuttcp"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Alban FRICOT <africot@toulouse.viveris.com>
'''


import re
import sys
import time
import syslog
import argparse
import subprocess
from itertools import repeat
from collections import defaultdict

import collect_agent


BRACKETS = re.compile(r'[\[\]]')


class AutoIncrementFlowNumber:
    def __init__(self):
        self.count = 0

    def __call__(self):
        self.count += 1
        return 'Flow{0.count}'.format(self)


def multiplier(unit, base):
    if unit == base:
        return 1
    if unit.startswith('M'):
        return 1024 * 1024
    if unit.startswith('K'):
        return 1024
    if unit.startswith('m'):
        return 0.001
    return 1


def _command_build_helper(flag, value):
    if value is not None:
        yield flag
        yield str(value)


def server(port):
    cmd = ['nuttcp', '-S']
    cmd.extend(_command_build_helper('-p', port))
    p = subprocess.run(cmd)
    sys.exit(p.returncode)

def client(udp, port):
    # Connect to collect_agent
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/nuttcp/'
            'nuttcp_rstats_filter.conf')
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    cmd = ['stdbuf', '-oL', 'nuttcp']
    cmd.extend(_command_build_helper('-p', port))

    # Read output, and send stats
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    flow_map = defaultdict(AutoIncrementFlowNumber())

    for flow_number in repeat(None):
        line = p.stdout.readline().decode()
        tokens = BRACKETS.sub('', line).split()
        if not tokens:
            if p.poll() is not None:
                break
            continue

        timestamp = int(time.time() * 1000)

        try:
            try:
                flow, duration, _, transfer, transfer_units, bandwidth, bandwidth_units, jitter, jitter_units, packets_stats, datagrams = tokens
                jitter = float(jitter)
                datagrams = float(datagrams[1:-2])
                lost, total = map(int, packets_stats.split('/'))
            except ValueError:
                udp = False
                flow, duration, _, transfer, transfer_units, bandwidth, bandwidth_units = tokens
            else:
                udp = True
            transfer = float(transfer)
            bandwidth = float(bandwidth)
            interval_begin, interval_end = map(float, duration.split('-'))
        except ValueError:
            # filter out non-stats lines
            continue

        if not transfer or interval_end - interval_begin > interval:
            # filter out lines covering the whole duration
            continue

        try:
            flow_number = flow_map[int(flow)]
        except ValueError:
            if flow.upper() != "SUM":
                continue

        statistics = {
                'sent_data': transfer * multiplier(transfer_units, 'Bytes'),
                'throughput': bandwidth * multiplier(bandwidth_units, 'bits/sec'),
        }
        if udp:
            statistics['jitter'] = jitter * multiplier(jitter_units, 's')
            statistics['lost_pkts'] = lost
            statistics['sent_pkts'] = total
            statistics['plr'] = datagrams
        collect_agent.send_stat(timestamp, suffix=flow_number, **statistics)


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
            '-S', '--server', action='store_true',
            help='Run in server mode')
    parser.add_argument(
            '-p', '--port', type=int,
            help='Set server port to listen on/connect to '
            'n (default 5201)')
    parser.add_argument(
            '-u', '--udp', action='store_true',
            help='Use UDP rather than TCP')

    # get args
    args = parser.parse_args()
    port = args.port
    udp = args.udp

    if args.server:
        server(port)
    else:
        client(port, udp)
