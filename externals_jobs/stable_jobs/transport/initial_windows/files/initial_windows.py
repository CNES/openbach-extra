#!/usr/bin/env python3

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


"""Sources of the Job initial_windows"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import os
import sys
import syslog
import argparse
import traceback
import contextlib
import subprocess

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

def main(network, gw, interface, initcwnd, initrwnd):
    cmd = ['ip', 'route', 'change', network]

    if gw is not None:
        cmd += ['via', str(gw)]
    cmd += ['dev', str(interface)]
    if initcwnd is not None:
        cmd += ['initcwnd', str(initcwnd)]
    if initrwnd is not None:
        cmd += ['initrwnd', str(initrwnd)]
    p = subprocess.run(cmd)
    if p.returncode:
        message = 'WARNING: \'{}\' exited with non-zero code'.format(
                ' '.join(cmd))


if __name__ == "__main__":
    with use_configuration('/opt/openbach/agent/jobs/initial_windows/initial_windows_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('network', type=str, help='The destination network')
        parser.add_argument('interface', help='Interface where to set the initial windows')
        parser.add_argument('-g', '--gw', type=str, help='The next hop of the route')
        parser.add_argument(
                '-i', '--initcwnd', type=int,
                help='Initial congestion window'
        )
        parser.add_argument(
                '-r', '--initrwnd', type=int, 
                help='Initial congestion receipt window'
        )
    
        # get args
        args = parser.parse_args()
        network = args.network
        gw = args.gw
        interface = args.interface
        initcwnd = args.initcwnd
        initrwnd = args.initrwnd
    
        main(network, gw, interface, initcwnd, initrwnd)
