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

TCP_STAT = re.compile(r'megabytes=(?P<data_sent>[0-9\.]+) real_sec=(?P<time>[0-9\.]+) rate_Mbps=(?P<rate>[0-9\.]+)( retrans=(?P<retransmissions>[0-9]+))? total_megabytes=(?P<total_data_sent>[0-9\.]+) total_real_sec=(?P<total_time>[0-9\.]+) total_rate_Mbps=(?P<mean_rate>[0-9\.]+)( retrans=(?P<total_retransmissions>[0-9]+))?')
TCP_END_STAT = re.compile(r'megabytes=[0-9\.]+ real_seconds=[0-9\.]+ rate_Mbps=[0-9\.]+')
UDP_STAT = re.compile(r'megabytes=(?P<data_sent>[0-9\.]+) real_sec=(?P<time>[0-9\.]+) rate_Mbps=(?P<rate>[0-9\.]+) drop=(?P<lost_pkts>[0-9]+) pkt=(?P<sent_pkts>[0-9]+) data_loss=(?P<data_loss>[0-9\.]+) total_megabytes=(?P<total_data_sent>[0-9\.]+) total_real_sec=(?P<total_time>[0-9\.]+) total_rate_Mbps=(?P<total_rate>[0-9\.]+) drop=(?P<total_lost_pkts>[0-9]+) pkt=(?P<total_sent_pkts>[0-9]+) data_loss=(?P<total_data_loss>[0-9\.]+)')
UDP_END_STAT = re.compile(r'megabytes=[0-9\.]+ real_seconds=[0-9\.]+ rate_Mbps=[0-9\.]+')

def _command_build_helper(flag, value):
    if value is not None:
        yield flag
        yield str(value)

def server(args):
    cmd = ['nuttcp', '-S', '--nofork']
    cmd.extend(_command_build_helper('-P', args.get('command_port')))
    p = subprocess.run(cmd)
    sys.exit(p.returncode)

def client(args):
    # Connect to collect_agent
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/nuttcp/'
            'nuttcp_rstats_filter.conf')
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    cmd = ['stdbuf', '-oL', 'nuttcp', '-fparse', '-frunningtotal']
    cmd.extend(('-r', ) if args.get('receiver') else '')
    cmd.extend(('-u', ) if args.get('udp') else '')
    cmd.extend(_command_build_helper('-P', args.get('command_port')))
    cmd.extend(_command_build_helper('-p', args.get('port')))
    cmd.extend(_command_build_helper('-w', args.get('buffer_size')))
    cmd.extend(_command_build_helper('-M', args.get('mss')))
    cmd.extend(_command_build_helper('-c', args.get('dscp')))
    cmd.extend(_command_build_helper('-N', args.get('n_streams')))
    cmd.extend(_command_build_helper('-T', args.get('duration')))
    cmd.extend(_command_build_helper('-R', args.get('rate_limit')))
    cmd.extend(_command_build_helper('-i', args.get('stats_interval')))
    cmd.extend((args.get('server_ip'), ))
    
    if args.get('udp'):
        STAT = UDP_STAT
        END_STAT = UDP_END_STAT
    else:
        STAT = TCP_STAT
        END_STAT = TCP_END_STAT

    # Launch client
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    while True:
        # Iterate while process is running
        if p.poll() is not None:
                break

        timestamp = int(time.time() * 1000)
        line = p.stdout.readline().decode()
        # Check for last line
        if END_STAT.search(line):
            break

        # Else, get stats and send them
        try:
            statistics = STAT.search(line).groupdict()
        except AttributeError:
            continue
        # Filter None values
        statistics = { k:v for k, v in statistics.items() if v is not None }

        # Convert units and cast to float
        statistics = {
                k: (
                    float(v)*1024*1024 if k in
                    {'data_sent', 'rate', 'mean_rate', 'total_data_sent'}
                    else float(v))
                for k, v in statistics.items()
        }
        collect_agent.send_stat(timestamp, **statistics)


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            '-s', '--server', action='store_true',
            help='Run in server mode')
    parser.add_argument(
            '-i', '--server-ip', type=str,
            help='Server IP address (client only)')
    parser.add_argument(
            '-P', '--command-port', type=int,
            help='Set server port to listen on/connect to '
            'n (default 5000)')
    parser.add_argument(
            '-p', '--port', type=int,
            help='Set server port for the data transmission'
            '(default 5001)')
    parser.add_argument(
            '-R', '--receiver', action='store_true',
            help='Launch client as receiver (else, transmitter). Only in client.')
    parser.add_argument(
            '-u', '--udp', action='store_true',
            help='Use UDP rather than TCP')
    parser.add_argument(
            '-b', '--buffer-size', type=int,
            help='The receive buffer size')
    parser.add_argument(
            '-m', '--mss', type=int,
            help='The MSS for data connection')
    parser.add_argument(
            '-c', '--dscp', type=str,
            help='The DSP value on data streams (t|T suffix for full TOS field)')
    parser.add_argument(
            '-n', '--n-streams', type=int, default=1,
            help='The number of streams')
    parser.add_argument(
            '-d', '--duration', type=int,
            help='The duration of the transmission')
    parser.add_argument(
            '-r', '--rate-limit', type=int,
            help='The transmit rate limit in Kbps')
    parser.add_argument(
            '-I', '--stats-interval', type=float, default=1,
            help='The stats interval')

    # get args
    args = parser.parse_args()
    args = vars(args)

    server_mode = args.pop('server')
    
    if server_mode:
        server(args)
    else:
        client(args)
