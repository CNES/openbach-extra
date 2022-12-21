#!/usr/bin/env python3

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


"""Sources of the Job set_tos"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David FERNANDES <david.fernandes@viveris.fr>
'''

import sys
import syslog
import argparse
import subprocess

import collect_agent


def main(action, chain, tos, in_interface=None, out_interface=None, protocol=None,
         destination=None, source=None, dport=None, sport=None):

    if action == 'add':
        action_flag = '-A'
    else:
        action_flag = '-D'

    cmd = ['iptables', '-t', 'mangle', action_flag, chain]
    if in_interface:
        cmd.extend(['-i', in_interface])
    if out_interface:
        cmd.extend(['-o', out_interface])
    if protocol:
        cmd.extend(['-p', protocol])
    if destination:
        cmd.extend(['-d', destination])
    if source:
        cmd.extend(['-s', source])
    if dport:
        cmd.extend(['--dport', str(dport)])
    if sport:
        cmd.extend(['--sport', str(sport)])

    cmd.extend(['-j', 'TOS', '--set-tos', tos])

    check_cmd = cmd.copy()
    check_cmd[3] = '-C'
    p = subprocess.run(check_cmd, stderr=subprocess.PIPE)
    rule_exists = p.returncode == 0

    if action == 'add' and rule_exists:
        message = 'The rule already exists'
        collect_agent.send_log(syslog.LOG_DEBUG, message)
        print(message)
        return

    if action == 'del' and not rule_exists:
        message = 'The rule does not exist'
        collect_agent.send_log(syslog.LOG_DEBUG, message)
        print(message)
        return

    p = subprocess.run(cmd, stderr=subprocess.PIPE)
    if p.returncode:
        message = "Error when executing command '{}': '{}'".format(' '.join(cmd), p.stderr.decode())
        collect_agent.send_log(syslog.LOG_ERR, message)
        print(message)
        sys.exit(message)


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/set_tos/set_tos_rstats_filter.conf'):
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
                'action', choices=['add','del'],
                help='Action to perform : add or delete the rule to mark the packets')
        parser.add_argument('tos', help='ToS value to set. Support decimal and hexadecimal values.')
    
        subparsers = parser.add_subparsers(
                title='Subcommand mode', dest='chain',
                help='Chain to apply the rule')
        subparsers.required = True
        parser_prerouting = subparsers.add_parser('PREROUTING', help='Apply ToS to PREROUTING chain')
        parser_postrouting = subparsers.add_parser('POSTROUTING', help='Apply ToS to POSTROUTING chain')
        parser_forward = subparsers.add_parser('FORWARD', help='Apply ToS to FORWARD chain')
    
        parser_prerouting.add_argument(
                '-i', '--in-interface',
                help='Name of the interface receiving the packet')
        parser_postrouting.add_argument(
                '-o', '--out-interface',
                help='Name of the interface delivering the packet')
        parser_forward.add_argument(
                '-i', '--in-interface',
                help='Name of the interface receiving the packet')
        parser_forward.add_argument(
                '-o', '--out-interface',
                help='Name of the interface delivering the packet')
    
        parser.add_argument(
                '-p', '--protocol',
                help='Set the protocol to filter if the prtotocol choice is other. '
                     'If nothing, the flag is set to all protocols')
        parser.add_argument(
                '-s', '--source',
                help='Source IP address. Can be a whole network using IP/netmask.')
        parser.add_argument(
                '-d', '--destination',
                help='Destination IP address. Can be a whole network using IP/netmask.')
        parser.add_argument(
                '--sport',
                help='Source port (if TCP or UDP). Can be a range using ":" as in 5000:5300.')
        parser.add_argument(
                '--dport',
                help='Destination port (if TCP or UDP). Can be a range using ":" as in 5000:5300.')
    
        args = vars(parser.parse_args())
    
        if not args['protocol'] or args['protocol'].upper() not in ['TCP', 'UDP']:
            del args['sport']
            del args['dport']
    
        main(**args)
