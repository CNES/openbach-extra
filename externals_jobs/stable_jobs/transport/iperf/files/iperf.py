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


"""Sources of the Job iperf"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import re
import sys
import time
import syslog
import argparse
import traceback
import contextlib
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
    if unit.startswith('G'):
        return 1024 * 1024 * 1024
    if unit.startswith('M'):
        return 1024 * 1024
    if unit.startswith('K'):
        return 1024
    if unit.startswith('m'):
        return 0.001
    collect_agent.send_log(syslog.LOG_ERR, 'Units of iperf metrics are not available/correct')
    return 1


def _command_build_helper(flag, value):
    if value is not None:
        yield flag
        yield str(value)


def client(
        client, interval, window_size, port, udp, bandwidth, duration,
        num_flows, cong_control, mss, tos, iterations):
    cmd = ['iperf', '-c', client]
    cmd.extend(_command_build_helper('-i', interval))
    cmd.extend(_command_build_helper('-w', window_size))
    cmd.extend(_command_build_helper('-p', port))
    cmd.extend(_command_build_helper('-i', interval))
    if udp:
        cmd.append('-u')
        cmd.extend(_command_build_helper('-b', bandwidth))
    else:
        cmd.extend(_command_build_helper('-Z', cong_control))
    cmd.extend(_command_build_helper('-t', duration))
    cmd.extend(_command_build_helper('-P', num_flows))
    cmd.extend(_command_build_helper('-M', mss))
    cmd.extend(_command_build_helper('-S', tos))

    for i in range(iterations):
        subprocess.run(cmd)
        time.sleep(10)


def server(interval, window_size, port, udp, rate_compute_time, num_flows, iterations):
    cmd = ['iperf', '-s']
    cmd.extend(_command_build_helper('-i', interval))
    cmd.extend(_command_build_helper('-w', window_size))
    cmd.extend(_command_build_helper('-p', port))
    cmd.extend(_command_build_helper('-P', num_flows))
    if udp:
        cmd.append('-u')
        
    total_rate = []
    for i in range(iterations):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        flow_map = defaultdict(AutoIncrementFlowNumber())
        ref = time.perf_counter()
        for flow_number in repeat(None):
            line = p.stdout.readline().decode()
            tokens = BRACKETS.sub('', line).split()
            if not tokens:
                if p.poll() is not None:
                    break
                continue
            timestamp = collect_agent.now()
            if len(tokens) > 1 and tokens[1][-1] == '-':
                tokens[1] = tokens[1] + tokens[2]
                del(tokens[2])
            if len(tokens) > 9 and tokens[9][-1] == '/':
                tokens[9] = tokens[9] + tokens[10]
                del(tokens[10])
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

            elapsed = time.perf_counter() - ref
            try:
                flow_number = flow_map[int(flow)]
            except ValueError:
                if flow.upper() != "SUM":
                    continue
                elif flow.upper() == "SUM" and elapsed > rate_compute_time:
                    total_rate.append(bandwidth * multiplier(bandwidth_units, 'bits/sec'))

            statistics = {
                    'sent_data': transfer * multiplier(transfer_units, 'Bytes'),
                    'throughput': bandwidth * multiplier(bandwidth_units, 'bits/sec'),
            }
            if udp:
                statistics['jitter'] = jitter * multiplier(jitter_units, 's')
                statistics['lost_pkts'] = lost
                statistics['sent_pkts'] = total
                statistics['plr'] = datagrams
            if num_flows == 1 and elapsed > rate_compute_time:
                total_rate.append(bandwidth * multiplier(bandwidth_units, 'bits/sec'))
            
            collect_agent.send_stat(timestamp, suffix=flow_number, **statistics)
        error_log = p.stderr.readline()
        if error_log:
            collect_agent.send_log(syslog.LOG_ERR, 'Error when launching iperf: {}'.format(error_log))
            sys.exit(1)
        p.wait()
        statistics = {}
        statistics['mean_total_rate'] = sum(total_rate)/len(total_rate)
        statistics['max_total_rate'] = max(total_rate)
        collect_agent.send_stat(timestamp, **statistics)
        time.sleep(3)


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/iperf/iperf_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
                '-s', '--server', action='store_true',
                help='Run in server mode')
        group.add_argument(
                '-c', '--client', type=str,
                help='Run in client mode and specify server IP address')
        parser.add_argument(
                '-i', '--interval', type=int, default=1,
                help='Pause *interval* seconds between '
                'periodic bandwidth reports')
        parser.add_argument(
                '-w', '--window-size', type=str,
                help='Socket buffer sizes in B[M/L]. For TCP, this sets the TCP '
                'window size (for server and client mode).')
        parser.add_argument(
                '-p', '--port', type=int,
                help='Set server port to listen on/connect to '
                'n (default 5001) (only for client mode)')
        parser.add_argument(
                '-u', '--udp', action='store_true',
                help='Use UDP rather than TCP (should be enabled on server and '
                'client mode)')
        parser.add_argument(
                '-b', '--bandwidth', type=str,
                help='Set target bandwidth to n [M/K]bits/sec (default '
                '1Mbit/sec). This setting requires UDP (-u).')
        parser.add_argument(
                '-t', '--time', type=float,
                help='Time in seconds to transmit for (default 10secs). '
                'This setting requires client mode.')
        parser.add_argument(
                '-n', '--num-flows', type=int, default=1,
                help='The number of parallel flows (default: 1). If specified, it '
                'should be given for client & server mode.')
        parser.add_argument(
                '-C', '--cong-control', type=str,
                help='The TCP congestion control algorithm to use (e.g. cubic, '
                'reno) (only for client mode).')
        parser.add_argument(
                '-M', '--mss', type=str,
                help='The TCP/SCTP maximum segment size (MTU - 40 bytes) (only for '
                'client mode).')
        parser.add_argument('-S', '--tos', type=str,
                help='Set the IP type of service. The usual prefixes for octal and '
                     'hex can be used, i.e. 52, 064 and 0x34 specify the same value '
                     '(only for client mode).')
        parser.add_argument(
                '-k', '--iterations', type=int, default=1,
                help='Number of test repetitions (on client and server)')
        parser.add_argument(
                '-e', '--rate_compute_time', type=int, default=0,
                help='The elasped time after which we begin to consider the rate '
                'measures for TCP mean calculation (default: 0 second) (only for server '
                'mode)')
    
        # get args
        args = parser.parse_args()
        interval = args.interval
        window_size = args.window_size
        port = args.port
        udp = args.udp
        rate_compute_time = args.rate_compute_time
        num_flows = args.num_flows
        iterations = args.iterations
    
        if args.server:
            server(interval, window_size, port, udp, rate_compute_time, num_flows,
                   iterations)
        else:
            bandwidth = args.bandwidth
            duration = args.time
            num_flows = args.num_flows
            cong_control = args.cong_control
            mss = args.mss
            tos = args.tos
            client(
                    args.client, interval, window_size, port, udp, bandwidth,
                    duration, num_flows, cong_control, mss, tos, iterations)
