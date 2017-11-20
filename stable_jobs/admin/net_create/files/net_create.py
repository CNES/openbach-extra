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


"""Sources of the Job net_create"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Oumaima ZERROUQ <oumaima.zerrouq@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import sys
import syslog
import argparse
import ipaddress
import subprocess

import collect_agent


def main(net_name, address, password, RCfile):
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/net_create/'
            'net_create_rstats_filter.conf')

    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job net_create')

    # Define variable net for pool address allocation
    net = address.rsplit('.', 1)

    # CREATE TEMPLATE
    with open('/tmp/{}.yml'.format(net_name), 'w') as template:
        template.write('''\
heat_template_version: 2013-05-23

description: Simple template to deploy a single network instance

resources:

 {0}:
   properties:
     admin_state_up: true
     name: {0}
     shared: false
   type: OS::Neutron::Net

 network_subnet:
   properties:
     allocation_pools:
     - end: {1[0]}.127
       start: {1[0]}.2
     cidr: {2}/24
     dns_nameservers: []
     enable_dhcp: true
     host_routes: []
     ip_version: 4
     name: {0}
     network_id:
       get_resource: {0}
   type: OS::Neutron::Subnet'''.format(net_name, net, address))

    # Create network
    try:
        subprocess.call('export OS_PASSWORD={0} && source {2} '
                        '&& heat stack-create {1} -f /tmp/{1}.yml'
                        .format(password, net_name, RCfile), shell=True,
                        executable='/bin/bash')
    except Exception as ex:
        message = 'ERROR: {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


if __name__ == '__main__':
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-n', '--net_name', type=str, help='')
    parser.add_argument('-a', '--address', type=ipaddress.ip_address, help='')
    parser.add_argument('-p', '--password', type=str, help='')
    parser.add_argument('-f', '--RCfile', type=str, help='')
    # get args
    args = parser.parse_args()
    net_name = args.net_name
    address = args.address
    password = args.password
    RCfile = args.RCfile

    main(net_name, address, password, RCfile)
