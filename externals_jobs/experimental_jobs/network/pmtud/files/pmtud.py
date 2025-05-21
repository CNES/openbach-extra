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


"""Sources of the Job pmtud"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import re
import sys
import syslog
import argparse
import subprocess
from math import floor

import collect_agent


ERROR = re.compile(r'local error: Message too long')


def main(dest, lowest, highest, count):
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting ifconfig pmtud')

    if lowest >= highest:
        collect_agent.send_log(
                syslog.LOG_ERR,
                'Highest value must be higher than lowest value.')
        sys.exit(1)

    def ping_passes(mtu):
        """ Check if a ping passes """
        cmd = ['ping', '-M', 'do', '-s', str(mtu), '-c', str(count), dest]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            output = e.output
        return ERROR.search(output.decode()) is None

    while True:
        middle = floor((lowest + highest)/2)

        if ping_passes(middle):
            lowest = middle
        else:
            highest = middle

        # Stop loop if there is less than 1 of difference
        if highest - lowest <= 1:
            break

    # Highest may pass. In this case, we are not certain that it is the
    # maximum value. Else, we are certain that lowest is the max MTU.
    if ping_passes(highest):
        collect_agent.send_log(syslog.LOG_WARNING, "Max MTU not in range")
        mtu = highest
    elif not ping_passes(lowest):
        collect_agent.send_log(syslog.LOG_WARNING, "No valid MTU in range")
        sys.exit()
    else:
        mtu = lowest

    collect_agent.send_stat(collect_agent.now(), mtu=mtu)


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/pmtud/pmtud_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('dest', type=str, help='Destination IP or URL')
        parser.add_argument(
                '-l', '--lowest', type=int, default=1,
                help='Lowest value to test')
        parser.add_argument(
                '-H', '--highest', type=int, default=1500,
                help='Highest value to test')
        parser.add_argument(
                '-c', '--count', type=int, default=1,
                help='Number of pings to perform per iteration')
    
        # get args
        args = parser.parse_args()
    
        main(args.dest, args.lowest, args.highest, args.count)
