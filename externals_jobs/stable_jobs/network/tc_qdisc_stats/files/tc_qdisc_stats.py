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


"""Sources of the Job tc_qdisc_stats"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Bastien TAURAN <bastien.tauran@toulouse.viveris.com>
'''

import re
import sys
import time
import syslog
import argparse
import subprocess

import collect_agent


def convert(value):
    match = re.fullmatch(r'(-?\d+\.?\d*)([GMKkmun])?', value)
    if not match:
        return 0.0

    base, unit = match.groups()
    if unit == 'G':
        return 1000000000 * float(base)
    elif unit == 'M':
        return 1000000 * float(base)
    elif unit in 'kK':
        return 1000 * float(base)
    elif unit == 'm':
        return float(base) / 1000
    elif unit == 'u':
        return float(base) / 1000000
    elif unit == 'n':
        return float(base) / 1000000000
    else:
        return float(base)


BRACKETS = re.compile(r'[\[\]]')


def send_stats(line, last_sent, current_node, collect_agent, interval_stats):
    statistics = {}

    try:
        #General stats
        ind = line.index('Sent')
        statistics['throughput'] = (8*convert(line[ind+1]) - last_sent[current_node])/interval_stats
        last_sent[current_node] = 8*convert(line[ind+1])
        statistics['cumulated_sent_bits'] = 8*convert(line[ind+1])
        statistics['cumulated_sent_packets'] = convert(line[ind+3])
        ind = line.index('(dropped')
        statistics['cumulated_dropped_packets'] = convert(line[ind+1][:-1])
        ind = line.index('backlog')
        statistics['backlog_bits'] = 8*convert(line[ind+1][:-1])
        statistics['backlog_pkts'] = 8*convert(line[ind+2][:-1])

        # CoDel stats
        if "codel" in line:
            ind = line.index('count')
            statistics['codel_count'] = convert(line[ind+1])
            ind = line.index('lastcount')
            statistics['codel_lastcount'] = convert(line[ind+1])
            ind = line.index('ldelay')
            statistics['codel_ldelay'] = convert(line[ind+1][:-1])
            ind = line.index('drop_next')
            statistics['codel_drop_next'] = convert(line[ind+1][:-1])
            ind = line.index('maxpacket')
            statistics['codel_maxpacket'] = convert(line[ind+1])

        # pie stats
        if "pie" in line:
            ind = line.index('prob')
            statistics['pie_prob'] = convert(line[ind+1])
            ind = line.index('delay')
            statistics['pie_current_delay'] = convert(line[ind+1][:-1])
            if "avg_dq_rate" in line:
                ind = line.index('avg_dq_rate')
                statistics['pie_avg_dq_rate'] = convert(line[ind+1])
            ind = line.index('pkts_in')
            statistics['pie_pkts_in'] = convert(line[ind+1])
            ind = line.index('dropped')
            statistics['pie_dropped'] = convert(line[ind+1])
            ind = line.index('maxq')
            statistics['pie_maxq'] = convert(line[ind+1])

    except ValueError as e:
        message = "Cannot parse statistics: {}".format(e)
        collect_agent.send_log(syslog.LOG_ERR, message)
        print("Cannot parse statistics:", e)
        sys.exit(message)

    collect_agent.send_stat(collect_agent.now(), suffix=current_node, **statistics)


def main(interface, qdisc_nodes, interval_stats):
    cmd = ['stdbuf', '-oL', 'tc', '-s', 'qdisc', 'show', 'dev', interface]
    last_sent = {qdisc_node:0 for qdisc_node in qdisc_nodes}
    read_this_line = False
    while True:
        line_read = []
        current_node = -1
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in p.communicate()[0].decode().split("\n"):
            tokens = BRACKETS.sub('', line).split()
            if not tokens:
                continue
            if tokens[0] == 'qdisc':
                read_this_line = False
                if line_read:
                    send_stats(line_read, last_sent, current_node, collect_agent, interval_stats)
                    line_read = []
            if tokens[2] in qdisc_nodes:
                current_node = tokens[2]
                read_this_line = True
            if read_this_line:
                line_read += tokens
        if line_read:
            send_stats(line_read, last_sent, current_node, collect_agent, interval_stats)
        time.sleep(interval_stats)

    p.wait()


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/tc_qdisc_stats/tc_qdisc_stats_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
                'interface', type=str,
                help='The interface to monitor')
        parser.add_argument(
                'qdisc_nodes', type=str, nargs='+',
                help='The qdisc nodes to monitor')
        parser.add_argument(
                '-i', '--interval_stats', type=float, default=1,
                help='Pause interval seconds between periodic reports. Can be a float (default=1s)')
    
        # Get args and call the appropriate function
        args = parser.parse_args()
        interface = args.interface
        qdisc_nodes = args.qdisc_nodes
        interval_stats = args.interval_stats
        main(interface, qdisc_nodes, interval_stats)
