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


"""Sources of the Job tcp_buffer"""


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

def main(name, min_size, size, max_size):
    # Connect to collect agent
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/tcp_buffer/'
            'tcp_buffer_rstats_filter.conf'
    )
    collect_agent.send_log(syslog.LOG_DEBUG, "Starting job tcp_buffer")

    cmd = "sysctl net.ipv4.tcp_{}=\'{} {} {}\'".format(name, min_size, size, max_size)
    rc = subprocess.call(cmd, shell=True)
    if rc:
        message = "WARNING \'{}\' exited with non-zero code".format(cmd)


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', help='The name of the tcp buffer to set')
    parser.add_argument('min_size', type=int, help='The minial size of the buffer')
    parser.add_argument('size', type=int, help='The size of the buffer')
    parser.add_argument('max_size', type=int, help='The maximum size of the buffer')

    # get args
    args = parser.parse_args()
    name = args.name
    min_size = args.min_size
    size = args.size
    max_size = args.max_size

    main(name, min_size, size, max_size)
