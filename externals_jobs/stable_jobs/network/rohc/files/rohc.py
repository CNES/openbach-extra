#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016−2023 CNES
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


"""Sources of the Job rohc"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Bastien TAURAN <bastien.tauran@viveris.fr>
 * David FERNANDES <david.fernandes@viveris.fr>
'''

import re
import sys
import time
import syslog
import os.path
import argparse
import subprocess

import collect_agent


BRACKETS = re.compile(r'[\[\]]')
INTERVAL = 1000 # in ms


def run_command(cmd):
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if p.returncode:
        message = "Error when executing command '{}': '{}'".format(
                    ' '.join(cmd), p.stderr.decode())
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    return p.returncode, p.stdout.decode()


def generate_command(remote_ip, local_ip, port, direction, behavior, cid_type, max_contexts, size):
    cmd = ['stdbuf', '-oL', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'rohc_src', 'rohc_tunnel')]
    cmd += ['rohc0', 'udp', 'remote', remote_ip, 'local', local_ip]
    cmd += ['port', str(port)]
    cmd += ['--dir', direction]
    cmd += ['--behavior', behavior]
    cmd += ['--cid_type', cid_type]
    cmd += ['--max_contexts', str(max_contexts)]
    cmd += ['--size', str(size)]
    return cmd


def collect_errors(p):
    error_log = p.stderr.readline().decode()
    if error_log:
        error_msg = ''
        while error_log:
            if 'signal 15' in error_log:
                continue
            error_msg += '{}     \n'.format(error_log)
            error_log = p.stderr.readline().decode()
        collect_agent.send_log(syslog.LOG_ERR, error_msg)
        exit(error_msg)


# Initialize a dict ready to store compression statistics
def init_comp_stats():
    stats = dict()
    stats['comp_total_uncompressed'] = 0
    stats['comp_total_compressed'] = 0
    stats['comp_cumulative_total_uncompressed'] = 0
    stats['comp_cumulative_total_compressed'] = 0
    stats['comp_total_ratio'] = 0
    stats['comp_cumulative_total_ratio'] = 0
    stats['comp_header_uncompressed'] = 0
    stats['comp_header_compressed'] = 0
    stats['comp_cumulative_header_uncompressed'] = 0
    stats['comp_cumulative_header_compressed'] = 0
    stats['comp_header_ratio'] = 0
    stats['comp_cumulative_header_ratio'] = 0
    stats['comp_segments'] = 0
    return stats


# Reinitialize some elements of the comp_stats dict
def reinit_comp_stats(stats):
   stats['comp_total_uncompressed'] = 0
   stats['comp_total_compressed'] = 0
   stats['comp_header_uncompressed'] = 0
   stats['comp_header_compressed'] = 0
   stats['comp_segments'] = 0
   return stats


# Initialize a dict ready to store decompression statistics
def init_decomp_stats():
    stats = dict()
    stats['decomp_lost'] = 0
    stats['decomp_failed'] = 0
    return stats


def main(remote_ip, local_ip, tunnel_ipv4, tunnel_ipv6, port, direction, behavior, cid_type, max_contexts, size):
    if behavior == 'nothing':
        behavior = 'no'

    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting rohc job')
    # Check there is not another ROHC tunnel established
    p = subprocess.run(['ip', 'l', 'show', 'rohc0'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if p.returncode == 0:
        message = "Error: Interface 'rohc0' already exists. A ROHC tunnel might be already established."
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    # Get shell command to launch ROHC binary
    cmd = generate_command(remote_ip, local_ip, port, direction, behavior, cid_type, max_contexts, size)
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    time.sleep(1)

    run_command(['ip', 'a', 'add', tunnel_ipv4, 'dev', 'rohc0'])
    run_command(['ip', '-6', 'a', 'add', tunnel_ipv6, 'dev', 'rohc0'])
    run_command(['ip', 'l', 'set', 'rohc0', 'up'])

    # Init local variables used to calculate statistics
    comp_stats = init_comp_stats()
    decomp_stats = init_decomp_stats()
    last_statistics_sent_comp = collect_agent.now()
    last_statistics_sent_decomp = collect_agent.now()
    number_of_stats_interval_comp = 0
    number_of_stats_interval_decomp = 0

    while True:
        # Get the logs of the ROHC binary
        line = p.stdout.readline().decode()
        tokens = BRACKETS.sub('', line).split()
        if not tokens:
            if p.poll() is not None:
                break
            continue

        # Parse the logs of the ROHC binary
        if tokens[0] == 'comp': # Calculate compression statistics
            number_of_stats_interval_comp += 1
            comp_stats['comp_total_uncompressed'] += int(tokens[4])
            comp_stats['comp_total_compressed'] += int(tokens[6])
            comp_stats['comp_header_uncompressed'] += int(tokens[5])
            comp_stats['comp_header_compressed'] += int(tokens[7])
            comp_stats['comp_segments'] += int(tokens[9])
            timestamp = collect_agent.now()

            if timestamp > last_statistics_sent_comp + INTERVAL and number_of_stats_interval_comp:
                last_statistics_sent_comp = timestamp
                comp_stats['comp_cumulative_total_uncompressed'] += comp_stats['comp_total_uncompressed']
                comp_stats['comp_cumulative_total_compressed'] += comp_stats['comp_total_compressed']
                comp_stats['comp_cumulative_header_uncompressed'] += comp_stats['comp_header_uncompressed']
                comp_stats['comp_cumulative_header_compressed'] += comp_stats['comp_header_compressed']
                comp_stats['comp_total_uncompressed'] /= number_of_stats_interval_comp
                comp_stats['comp_total_compressed'] /= number_of_stats_interval_comp
                comp_stats['comp_header_uncompressed'] /= number_of_stats_interval_comp
                comp_stats['comp_header_compressed'] /= number_of_stats_interval_comp
                comp_stats['comp_segments'] /= number_of_stats_interval_comp
                comp_stats['comp_total_ratio'] = comp_stats['comp_total_compressed']/comp_stats['comp_total_uncompressed']
                comp_stats['comp_header_ratio'] = comp_stats['comp_header_compressed']/comp_stats['comp_header_uncompressed']
                comp_stats['comp_cumulative_total_ratio'] += comp_stats['comp_total_ratio']
                comp_stats['comp_cumulative_header_ratio'] += comp_stats['comp_header_ratio']

                collect_agent.send_stat(timestamp, **comp_stats)

                number_of_stats_interval_comp = 0
                compt_stats = reinit_comp_stats(comp_stats)

        # Calculate decompression statistics
        if tokens[0] == 'decomp':
            decomp_stats = init_decomp_stats()
            decomp_stats['decomp_lost'] = float(tokens[3])
            decomp_stats['decomp_failed'] = float(tokens[4])
            number_of_stats_interval_decomp = 1
            timestamp = collect_agent.now()

            if timestamp > last_statistics_sent_decomp + INTERVAL and number_of_stats_interval_decomp:
                last_statistics_sent_decomp = timestamp
                collect_agent.send_stat(timestamp, **decomp_stats)
                number_of_stats_interval_decomp = 0

    # Get errors from the logs and send them to the collector
    collect_errors(p)
    p.wait()


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/rohc/rohc_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('remote_ip', type=str, help='The remote IP address')
        parser.add_argument('local_ip', type=str, help='The local IP address')
        parser.add_argument('tunnel_ipv4', type=str, help='The IPv4 address of the tunnel')
        parser.add_argument('tunnel_ipv6', type=str, help='The IPv6 address of the tunnel')
        parser.add_argument('--port', '-p', type=int, default=5000,
                            help='The port used for local and remote address')
        parser.add_argument('--direction', '-d', type=str, default='bidirectional', choices=['unidirectional', 'bidirectional'],
                            help='Choose bidirectional to add feedback from decompressor to compressor')
        parser.add_argument('--behavior', '-b', type=str, default='both', choices=['send', 'receive', 'both', 'nothing'],
                            help='Choose which tasks to do in this job')
        parser.add_argument('--cid-type', '-c', type=str, default='largecid', choices=['smallcid', 'largecid'],
                            help='Handle small or large CIDs')
        parser.add_argument('--max-contexts', '-m', type=int, default=16,
                            help='Maximum number of contexts')
        parser.add_argument('--size', '-s', type=int, default=1500,
                            help='Maximum size of ROHC packets, not including the UDP tunnel offset')

        args = vars(parser.parse_args())
        main(**args)
