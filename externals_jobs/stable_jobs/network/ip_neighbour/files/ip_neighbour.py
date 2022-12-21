#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016−2023 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
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


"""Sources of the Job ip_neighbour"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Bastien TAURAN <bastien.tauran@viveris.fr>
'''

import sys
import syslog
import argparse
import subprocess

import collect_agent


OPERATIONS = {'add', 'change', 'replace', 'delete'}


def main(operation, destination_ip, mac_address, device):
    command = ['ip', 'neighbour', operation, destination_ip]

    if operation != 'delete':
        command.extend(['lladdr', mac_address])

    command.extend(['dev', device])

    try:
        p = subprocess.run(command, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as ex:
        message = 'ERROR: {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    if p.returncode:
        error = p.stderr.decode()
        if any(err in error for err in {'File exists', 'No such process'}):
            message = 'WARNING: {} exited with non-zero return value ({}): {}'.format(
                command, p.returncode, error)
            collect_agent.send_log(syslog.LOG_WARNING, message)
            sys.exit(0)
        else:
            message = 'ERROR: {} exited with non-zero return value ({})'.format(
                command, p.returncode)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)
    else:
        collect_agent.send_log(
                syslog.LOG_DEBUG,
                '{} route {}'.format(operation, destination_ip))


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/ip_neighbour/ip_neighbour_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                 description=__doc__,
                 formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument('operation', choices=OPERATIONS, help='The operation to apply')
        parser.add_argument('device', type=str, help='The output device name')
        parser.add_argument('destination_ip', type=str, help='The destination IP address')
        parser.add_argument('mac_address', type=str, help='The corresponding MAC address')
          
        args = vars(parser.parse_args())
        main(**args)
