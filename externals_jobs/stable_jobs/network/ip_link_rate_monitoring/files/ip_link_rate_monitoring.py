#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2022 Eutelsat
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


"""Sources of the Job ip_link_rate_monitoring"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Bastien TAURAN <bastien.tauran@viveris.fr>
'''

import os
import sys
import time
import syslog
import argparse
import traceback
import subprocess
import contextlib

import collect_agent


def run_command(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as err:
        message = "Error when executing command '{}': '{}'".format(' '.join(cmd), p.stderr)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


def ip_link(interface):
    lines = run_command('ip', '-s', 'link', 'show', 'dev', interface).splitlines()
    for i, line in enumerate(lines):
        if 'TX' in line:
            tx = map(int, lines[i+1].split())
        if 'RX' in line:
            rx = map(int, lines[i+1].split())

    return list(tx)[:4], list(rx)[:4]


def parse_interval(new_values, old_values, interval):
    diff = [new - old for new, old in zip(new_values, old_values)]
    diff.append(diff[0] / interval)
    diff.append(diff[1] / interval)
    return diff


def main(interface, interval):
    last_tx, last_rx = ip_link(interface)

    while True:
        tx, rx = ip_link(interface)
        tx_stats = parse_interval(tx, last_tx, interval)
        rx_stats = parse_interval(rx, last_rx, interval)

        collect_agent.send_stat(
                collect_agent.now(),
                suffix=interface,
                tx_bits_in_interval=tx_stats[0] * 8,
                tx_pkts_in_interval=tx_stats[1],
                tx_errors_in_interval=tx_stats[2],
                tx_drops_in_interval=tx_stats[3],
                tx_rate_bits=tx_stats[4] * 8,
                tx_rate_pkts=tx_stats[5],
                rx_bits_in_interval=rx_stats[0] * 8,
                rx_pkts_in_interval=rx_stats[1],
                rx_errors_in_interval=rx_stats[2],
                rx_drops_in_interval=rx_stats[3],
                rx_rate_bits=rx_stats[4] * 8,
                rx_rate_pkts=rx_stats[5],
        )

        last_tx = tx
        last_rx = rx

        time.sleep(interval)


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/ip_link_rate_monitoring/ip_link_rate_monitoring_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument('interface', type=str, help='The interface to monitor.')
        parser.add_argument('-i', '--interval', type=int, default=1, help='Interval for statistics in seconds.')

        args = parser.parse_args()

        main(args.interface, args.interval)
