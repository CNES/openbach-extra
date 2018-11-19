#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2018 CNES
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

"""Sources of the voip_qoe_dest OpenBACH job"""

__author__ = 'Antoine AUGER'
__credits__ = 'Antoine AUGER <antoine.auger@tesa.prd.fr>'

import argparse
import os
import subprocess
import syslog
import collect_agent

job_name = "voip_qoe_dest"
common_prefix = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))  # /opt/openbach/agent/jobs


def build_parser():
    """
    Method used to validate the parameters supplied to the program

    :return: an object containing required/optional arguments with their values
    :rtype: object
    """
    parser = argparse.ArgumentParser(description='Start a receiver (destination) component to measure QoE of one or '
                                                 'many VoIP sessions generated with D-ITG software',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    return parser


def main():
    """
    Main method

    :return: nothing
    """
    success = collect_agent.register_collect(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                          '{}_rstats_filter.conf'.format(job_name)))
    if not success:
        message = 'Could not connect to rstats'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)

    process = subprocess.Popen([os.path.join(common_prefix, job_name, 'D-ITG-2.8.1-r1023', 'bin', 'ITGRecv')],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        output = process.stdout.readline().decode().strip()
        if not output:
            if process.poll is not None:
                break
            continue
        if output != "Press Ctrl-C to terminate":
            collect_agent.send_log(syslog.LOG_DEBUG, output)
        print(output)

    msg = "ITGRecv has exited with the following return code: {}".format(output)  # Output contains return code
    collect_agent.send_log(syslog.LOG_DEBUG, msg)


if __name__ == "__main__":
    # No internal configuration needed for receiver side
    # Argument parsing
    args = build_parser().parse_args()
    main()
