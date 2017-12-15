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


"""Sources of the Job initial_spreading_fq"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import sys
import syslog
import argparse
import subprocess
import collect_agent

def main(rate, interfaces, disable_pacing):
    # Connect to collect_agent
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/initial_spreading_fq/'
            'initial_spreading_fq_rstats_filter.conf')
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job '
            'initial_spreading_fq')

    # Set spreading rate
    cmd = ['sysctl',  'net.ipv4.tcp_initial_spreading_rate_min={}'.format(rate)]
    p = subprocess.run(cmd)
    if p.returncode:
        message = 'WARNING: \'{}\' returned non-zero code'.format(
                ' '.join(cmd))
        collect_agent.send_log(syslog.LOG_WARNING, message)

    # Add FQ tc on interfaces
    for interface in interfaces:
        cmd = ['tc', 'qdisc', 'add', 'dev', interface, 'root', 'fq']
        p = subprocess.run(cmd)
        if p.returncode:
            message = 'WARNING: \'{}\' returned non-zero code'.format(' '.join(cmd))
            collect_agent.send_log(syslog.LOG_WARNING, message)

    # Enable or disable pacing
    pacing = 1 if disable_pacing else 0
    cmd = ['sysctl', 'net.ipv4.tcp_disable_pacing={}'.format(pacing)]
    p = subprocess.run(cmd)
    if p.returncode:
        message = 'WARNING: \'{}\' returned non-zero code'.format(
                ' '.join(cmd))
        collect_agent.send_log(syslog.LOG_WARNING, message)


if __name__ == '__main__':
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            'rate', type=int,
            help='Tcp initial spreading minimal rate')
    parser.add_argument(
            'interfaces', type=str, nargs='+',
            help='The interfaces, separated by spaces, where'
            ' the initial spreading fq is set')
    parser.add_argument(
            '-d', '--disable-pacing', action='store_true',
            help='Disable pacing')

    # get args
    args = parser.parse_args()
    rate = args.rate
    interfaces = args.interfaces
    disable_pacing = args.disable_pacing

    main(rate, interfaces, disable_pacing)
