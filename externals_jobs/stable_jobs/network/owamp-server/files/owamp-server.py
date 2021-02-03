#!/usr/bin/env python3
#  OpenBACH is a generic testbed able to control/configure multiple
#  network/physical entities (under test) and collect data from them. It is
#  composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#  Agents (one for each network entity that wants to be tested).
#
#
#  Copyright © 2016-2020 CNES
#
#
#  This file is part of the OpenBACH testbed.
#
#
#  OpenBACH is a free software : you can redistribute it and/or modify it under
#  the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
#  any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#  more details. # # You should have received a copy of the GNU General Public License along with
#  this program. If not, see http://www.gnu.org/licenses/.


"""Sources of the Job owamp-server"""


__author__ = 'Silicom'
__credits__ = '''Contributor: Marlene MOST <mmost@silicom.fr>'''


import os
import signal
import syslog
import argparse
import traceback
import subprocess
import contextlib
from sys import exit
from time import sleep

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


def build_parser():
    parser = argparse.ArgumentParser(description='', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-S', type=str, dest='server_address', help='IP address of the server')

    return parser


def stop_server(sig, frame):
    # stop daemon when job instance stopped
    stop_cmd = ['pkill', '-SIGTERM', 'owamp']
    subprocess.run(stop_cmd)

    exit(0)


def server(server_address):
    # launch daemon using sudo /usr/sbin/owampd -c /etc/owamp-server -U owamp
    launch_cmd = ['sudo', '/usr/sbin/owampd', '-c', '/etc/owamp-server', '-U', 'owamp']

    if server_address:
        # use option -S @server_ip
        launch_cmd += ['-S', server_address]

    subprocess.run(launch_cmd)

    # function still running until job instance has stopped
    # wait for job termination to stop daemon
    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGTERM, stop_server)

    # make job persistent
    while True:
        sleep(1)


if __name__ == '__main__':
    with use_configuration('/opt/openbach/agent/jobs/owamp-server/server_rstats_filter.conf'):
        args = build_parser().parse_args()
        server(args.server_address)




