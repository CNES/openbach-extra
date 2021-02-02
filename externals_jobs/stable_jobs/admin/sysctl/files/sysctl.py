#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2020 CNES
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


""" Sources of the job sysctl """

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import os
import sys
import syslog
import argparse
import traceback
import subprocess
import contextlib
import collect_agent

@contextlib.contextmanager
def use_configuration(filepath):
    success = collect_agent.register_collect(filepath)
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job ' + os.environ.get('JOB_NAME', '!'))
    try:
        yield
    except Exception:
        message = traceback.format_exc()
        collect_agent.send_log(syslog.LOG_CRIT, message)
        raise
    except SystemExit as e:
        if e.code != 0:
            collect_agent.send_log(syslog.LOG_CRIT, 'Abrupt program termination: ' + str(e.code))
        raise

def main(param, value):
    shell = False
    cmd = ['sysctl', '{}={}'.format(param, value)]
    if len(value.split()) > 1:
        cmd = ' '.join(cmd)
        shell = True
    try:
        p = subprocess.run(cmd, shell=shell)
    except Exception as ex:
        collect_agent.send_log(syslog.LOG_ERR,
                               "ERROR modifying sysctl {}:{}".format(param, ex))
    if p.returncode == 0:
        collect_agent.send_log(syslog.LOG_DEBUG,
                               "syscll {} set to {}".format(param, value))
    else:
        collect_agent.send_log(syslog.LOG_ERR, "Wrong return code")
            

if __name__ == "__main__":
    with use_configuration('/opt/openbach/agent/jobs/sysctl/sysctl_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(description='',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('param', metavar='param', type=str,
                            help='The sysctl parameter name')
        parser.add_argument('value', metavar='value', type=str, 
                            help='The sysctl parameter desired value')
    
        # get args
        args = parser.parse_args()
        param = args.param
        value = args.value
        
        main(param, value)
    
