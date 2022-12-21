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

"""Sources of the Job pep"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
 * David FERNANDES <david.fernandes@viveris.fr>
'''


import os
import re
import sys
import syslog
import argparse
import subprocess

os.environ['XTABLES_LIBDIR'] = '$XTABLES_LIBDIR:/usr/lib/x86_64-linux-gnu/xtables' # Required for Ubuntu 20.04
import iptc

import collect_agent


def run_command(command):
    try:
        p = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except Exception as ex:
        message = 'ERROR: {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    if p.returncode:
        error = p.stderr.decode()
        if 'del' in command and ('No such file' in error or 'No such process' in error):
            message = 'WARNING: {} exited with non-zero return value ({}): {}'.format(
                command, p.returncode, error)
            collect_agent.send_log(syslog.LOG_WARNING, message)
            print(message)
        else:
            if 'add' in command and 'File exists' in error:
                message = 'ERROR: the route to add ({}) already exists. A pepsal instance might be already running'.format(command)
            else:
                message = 'ERROR: {} exited with non-zero return value ({}): {}'.format(command, p.returncode, error)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)
    else:
        collect_agent.send_log(syslog.LOG_DEBUG, 'Command applied successfully : ' + ' '.join(command))

    return p.returncode


def manage_rule(chain, action, port, mark, in_iface=None, ip_src=None, ip_dst=None):
    rule = iptc.Rule()
    rule.protocol = 'tcp'
    rule.create_target('TPROXY')
    rule.target.set_parameter('on_port', str(port))
    rule.target.set_parameter('tproxy_mark', str(mark))
    if in_iface is not None:
        rule.in_interface = str(in_iface)
    if ip_src is not None:
        rule.src = str(ip_src)
    if ip_dst is not None:
        rule.dst = str(ip_dst)

    try:
        if action == 'add':
            chain.append_rule(rule)
        elif action == 'del':
            chain.delete_rule(rule)
        else:
            message = 'Internal Error : Bad rule action'
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)

    except iptc.ip4tc.IPTCError as ex:
        message = 'ERROR: {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


def set_conf(ifaces, src_ip, dst_ip, port, mark, table_num, unset=False):
    action = 'del' if unset else 'add'

    # Set (or unset) routing configuration for PEPSal
    cmd = ['ip', 'route', action, 'local', '0.0.0.0/0', 'dev', 'lo', 'table', str(table_num)]
    run_command(cmd)
    cmd = ['ip', 'rule', action, 'fwmark', str(mark), 'lookup', str(table_num)]
    run_command(cmd)

    # Get PREROUTING chain of mangle table
    table = iptc.Table(iptc.Table.MANGLE)
    target_chain = None
    for chain in table.chains:
        if chain.name == 'PREROUTING':
            target_chain = chain
            break
    if target_chain is None:
        message = 'ERROR could not find chain PREROUTING of MANGLE table'
        collect_agent.send_log(syslog.LOG_ERROR, message)
        sys.exit(message)
        print(message)

    for iface in ifaces:
        manage_rule(target_chain, action, port, mark, in_iface=iface)

    for ip in src_ip:
        manage_rule(target_chain, action, port, mark, ip_src=ip)

    for ip in dst_ip:
        manage_rule(target_chain, action, port, mark, ip_dst=ip)


def main(ifaces, src_ip, dst_ip, stop, port, addr, fopen, maxconns,
         gcc_interval, log_file, pending_time, mark, table_num):
    if stop:
        # unset routing configuration
        set_conf(ifaces, src_ip, dst_ip, port, mark, table_num, unset=True)
    else:
        # set routing conf
        set_conf(ifaces, src_ip, dst_ip, port, mark, table_num)

        # stop pepsal service
        cmd = ['systemctl', 'stop', 'pepsal.service']
        run_command(cmd)
        collect_agent.send_log(syslog.LOG_DEBUG, 'pepsal.service stopped')

        # launch pepsal
        cmd = [
                'pepsal', str(fopen), '-p', str(port),
                '-a', str(addr), '-c', str(maxconns),
                '-g', str(gcc_interval), '-l', str(log_file),
                '-t', str(pending_time),
        ]
        try:
            p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        except Exception as ex:
            set_conf(ifaces, src_ip, dst_ip, port, mark, table_num, unset=True)
            message = 'ERROR: {}'.format(ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)

        if p.returncode:
            set_conf(ifaces, src_ip, dst_ip, port, mark, table_num, unset=True)
            message = 'ERROR: {} exited with non-zero return value ({}): {}'.format(
                cmd, p.returncode, p.stderr.decode())
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)
        else:
            collect_agent.send_log(syslog.LOG_DEBUG, 'PEP launched successfully')


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/pep/pep_rstat_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(description='',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-p', '--port', type=int, default=5000,
                help='The port PEPsal uses to listen for incoming connection')
        parser.add_argument('-a', '--address', type=str, default='0.0.0.0',
                help='The address PEPsal uses to bind the listening socket')
        parser.add_argument('-f', '--fastopen', action='store_true',
                help='Enable TCP FastOpen')
        parser.add_argument('-c', '--maxconns', type=int, default=2112,
                help='The maximum number of simultaneous connections')
        parser.add_argument('-g', '--gcc-interval', type=int, default=54000,
                help='The garbage collector interval')
        parser.add_argument('-l', '--log-file', type=str, default='/var/log/pepsal/connections.log',
                help='The connections log path')
        parser.add_argument('-t', '--pending-lifetime', type=int, default=18000,
                help='The pending connections lifetime')
        parser.add_argument('-x', '--stop', action='store_true',
                help='If set, unset routing configuration')
        parser.add_argument('-i', '--redirect-ifaces', type=str, default='',
                help="Redirect all traffic from incoming interfaces to PEPsal (admits multiple interfaces separated by ',' ' ')")
        parser.add_argument('-s', '--redirect-src-ip', type=str, default='',
                help="Redirect all traffic with src IP to PEPsal (admits multiple IPs separated by ',' ' ')")
        parser.add_argument('-d', '--redirect-dst-ip', type=str, default='',
                help="Redirect all traffic with dest IP to PEPsal (admits multiple IPs separated by ',' ' ')")
        parser.add_argument('-m', '--mark', type=int, default=1,
                help='The mark used for routing packets to the PEP')
        parser.add_argument('-T', '--table-num', type=int, default=100,
                help='The routing table number used for routing packets to the PEP')

        # get args
        args = parser.parse_args()
        port = args.port
        addr = args.address
        fopen = '-f' if args.fastopen else ''
        maxconns = args.maxconns
        gcc_interval = args.gcc_interval
        log_file = args.log_file
        pending_time = args.pending_lifetime
        ifaces = re.findall(r'[^\,\ \t]+', args.redirect_ifaces)
        src_ip = re.findall(r'[^\,\ \t]+', args.redirect_src_ip)
        dst_ip = re.findall(r'[^\,\ \t]+', args.redirect_dst_ip)
        stop = args.stop
        mark = args.mark
        table_num = args.table_num

        main(ifaces, src_ip, dst_ip, stop, port, addr, fopen, maxconns,
             gcc_interval, log_file, pending_time, mark, table_num)
