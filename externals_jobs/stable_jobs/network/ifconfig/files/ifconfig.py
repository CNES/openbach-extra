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


"""Sources of the Job ifconfig"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Oumaima ZERROUQ <oumaima.zerrouq@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import os
import sys
import syslog
import argparse
import ipaddress
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

def main(interface_name, ip_address, action):
    if action == 1:
        # Add an ip add
        try:
            subprocess.check_call(['ifconfig', interface_name, str(ip_address)])
            collect_agent.send_log(syslog.LOG_DEBUG, 'New ip address added')
        except Exception as ex:
            message = 'ERROR {}'.format(ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)

        with open('/etc/network/interfaces') as interfaces:
            content = interfaces.readlines()

        found_iface = None
        found_address = False
        last_seen_interface_name = None
        for index, line in enumerate(content):
            liste = line.split()
            if liste and liste[0] == 'iface':
                last_seen_interface_name = liste[1]
                if last_seen_interface_name == interface_name:
                    content[index] = 'iface {} inet static\n'.format(interface_name)
                    found_iface = index

            if last_seen_interface_name == interface_name and liste and liste[0] == 'address':
                content[index] = '    address {}\n'.format(ip_address)
                found_address = True

        if found_iface is None:
            content += [
                    '\n', 'auto {}\n'.format(interface_name),
                    'iface {} inet static\n'.format(interface_name),
                    '    address {}\n'.format(ip_address),
                    '    netmask 255.255.255.0\n',
            ]
        elif not found_address:
            content.insert(found_iface + 1, '    address {}\n'.format(ip_address))

        with open('/etc/network/interfaces', 'w') as interfaces:
            interfaces.writelines(content)
    else:
        # Delete an interface's ip address
        try:
            subprocess.check_call(['ifconfig', interface_name, '0'])
            collect_agent.send_log(syslog.LOG_DEBUG, 'ip address deleted')
        except Exception as ex:
            message = 'ERROR {}'.format(ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)


if __name__ == '__main__':
    with use_configuration('/opt/openbach/agent/jobs/ifconfig/ifconfig_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('interface_name', type=str, help='')
        parser.add_argument(
                '-i', '--ip_address', type=ipaddress.ip_address,
                help='')
        parser.add_argument('-a', '--action', type=int, default=1, help='')
    
        # get args
        args = parser.parse_args()
        interface_name = args.interface_name
        ip_address = args.ip_address
        action = args.action
    
        main(interface_name, ip_address, action)
