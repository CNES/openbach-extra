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


"""Sources of the Job smartiw"""


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


def main(size, disable_pacing):
    # Connect to collect agent
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/smart_iw/'
            'smart_iw_rstats_filter.conf')
    collect_agent.send_log(syslog.LOG_DEBUG, "Starting job smart_iw")

    cmd = ['sysctl', 'net.ipv4.tcp_smart_iw={}'.format(size)]
    rc = subprocess.call(cmd)
    if rc:
        message = "WARNING \'{}\' exited with non-zero code".format(
                ' '.join(cmd))

    pacing = 1 if disable_pacing else 0
    cmd = ['sysctl', 'net.ipv4.tcp_disable_pacing={}'.format(pacing)]
    rc = subprocess.call(cmd)
    if rc:
        message = "WARNING \'{}\' exited with non-zero code".format(
                ' '.join(cmd))


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            'size', type=int,
            help='The size of the smart initial window')
    parser.add_argument(
            '-d', '--disable-pacing', action='store_true',
            help='Disable pacing')

    # get args
    args = parser.parse_args()
    size = args.size
    disable_pacing = args.disable_pacing

    main(size, disable_pacing)
