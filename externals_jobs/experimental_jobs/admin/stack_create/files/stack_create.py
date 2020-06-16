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


"""Sources of the Job stack_create"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Oumaima ZERROUQ <oumaima.zerrouq@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import sys
import syslog
import argparse
import subprocess

import collect_agent


def main(stack_name, flavor, image_id, network, password, RCfile):
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/stack_create/'
            'stack_create_rstats_filter.conf')

    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job stack_create')

    # Create var nets for adding networks
    text = '- network: {}'.format
    nets = '\n        '.join(map(text, network))

    with open('/tmp/{}.yml'.format(stack_name), 'w') as template:
        template.writelines('''\
heat_template_version: 2015-04-30

description: Simple template to deploy a single compute instance

resources:
  {0}:
    type: OS::Nova::Server
    properties:
      image : {1}
      flavor: {2}
      networks:
        {3}'''.format(stack_name, image_id, flavor, nets))

    # Create stack
    try:
        subprocess.call('export OS_PASSWORD={0} && source {2} '
                        '&& heat stack-create {1} -f /tmp/{1}.yml'
                        .format(password, stack_name, RCfile),
                        shell=True, executable='/bin/bash')
        collect_agent.send_log(syslog.LOG_DEBUG, 'New stack added')
    except Exception as ex:
        message = 'ERROR: {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


if __name__ == '__main__':
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--stack_name', type=str, help='')
    parser.add_argument('-f', '--flavor', type=str, help='')
    parser.add_argument('-i', '--image_id', type=str, help='')
    parser.add_argument('-n', '--network', nargs='*', type=str, help='')
    parser.add_argument('-p', '--password', type=str, help='')
    parser.add_argument('-r', '--RCfile', type=str, help='')

    # get args
    args = parser.parse_args()
    stack_name = args.stack_name
    flavor = args.flavor
    image_id = args.image_id
    network = args.network
    password = args.password
    RCfile = args.RCfile

    main(stack_name, flavor, image_id, network, password, RCfile)
