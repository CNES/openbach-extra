#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2020 CNES
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


import argparse
import subprocess


def main(log_buffer_size):

    if log_buffer_size:
        cmd = '/opt/openbach/agent/jobs/d-itg_recv/d-itg/bin/ITGRecv -q {}'.format(log_buffer_size)
    else:
        cmd = '/opt/openbach/agent/jobs/d-itg_recv/d-itg/bin/ITGRecv'

    subprocess.call(cmd, shell=True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create a D-ITG command',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-q', '--log_buffer_size', type=int, metavar='LOG BUFFER SIZE',
                        help='Number of packets to push to the log at once (Default: 50)')

    # get args
    args = parser.parse_args()
    log_buffer_size = args.log_buffer_size 

    main(log_buffer_size)
