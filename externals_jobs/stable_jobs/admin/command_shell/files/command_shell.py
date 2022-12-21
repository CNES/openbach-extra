#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
# OpenBACH is a free software : you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
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


""" Sources of the job command_shell """

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David PRADAS <david.pradas@toulouse.viveris.com>
'''


import syslog
import argparse
import subprocess

import collect_agent


def main(command_line):
    try:
        p = subprocess.run(command_line, stderr=subprocess.PIPE, shell=True)
    except Exception as ex:
        collect_agent.send_log(syslog.LOG_ERR,
                               "ERROR launching command line {}:{}".format(command_line, ex))
    if p.returncode == 0:
        collect_agent.send_log(syslog.LOG_DEBUG,
                               "Command line launched: {}".format(command_line))
    else:
        collect_agent.send_log(syslog.LOG_ERR, "ERROR on command line: {}".format(p.stderr))
            

if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/command_shell/command_shell_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(description='',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('command_line', metavar='param', type=str,
                            help='The command line to execute in shell')
    
        # get args
        args = parser.parse_args()
        command_line = args.command_line
        
        main(command_line)
