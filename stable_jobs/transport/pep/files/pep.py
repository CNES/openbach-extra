#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
'''


import argparse
import subprocess
import syslog
import collect_agent
import sys
import iptc

def set_conf(ifaces, src_ip, dst_ip, port, mark, table_num, unset=False):
    # Set (or unset) routing configuration for PEPSal
    cmd = [
            'ip', 'rule', 'del' if unset else 'add',
            'fwmark', str(mark), 'lookup', str(table_num)
    ]
    rc = subprocess.call(cmd)
    if rc:
        message = "WARNING \'{}\' exited with non-zero code".format(
                ' '.join(cmd))
        collect_agent.send_log(syslog.LOG_WARNING, message)

    cmd = [
            'ip', 'route', 'del' if unset else 'add',
            'local', '0.0.0.0/0', 'dev', 'lo', 'table',
            str(table_num)
    ]
    rc = subprocess.call(cmd)
    if rc:
        message = "WARNING \'{}\' exited with non-zero code".format(
                ' '.join(cmd))
        collect_agent.send_log(syslog.LOG_WARNING, message)

    # Get PREROUTING chain of mangle table
    table = iptc.Table(iptc.Table.MANGLE)
    target_chain = None
    for chain in table.chains:
        if chain.name == "PREROUTING":
            target_chain = chain
            break
    if target_chain is None:
        message = "ERROR could not find chain PREROUTING of MANGLE table"
        collect_agent.send_log(syslog.LOG_ERROR, message)
        sys.exit(message)
 
    for iface in ifaces:
        rule = iptc.Rule()
        rule.protocol = "tcp"
        rule.in_interface = str(iface)
        rule.create_target("TPROXY")
        rule.target.set_parameter("on_port", str(port))
        rule.target.set_parameter("tproxy_mark", str(mark))
        try:
            if not unset:
                target_chain.append_rule(rule)
            else:
                target_chain.delete_rule(rule)
        except iptc.ip4tc.IPTCError as ex:
            message = "WARNING \'{}\'".format(ex)
            collect_agent.send_log(syslog.LOG_WARNING, message)

    for ip in src_ip:
        rule = iptc.Rule()
        rule.protocol = "tcp"
        rule.src = str(ip)
        rule.create_target("TPROXY")
        rule.target.set_parameter("on_port", str(port))
        rule.target.set_parameter("tproxy_mark", str(mark))
        try:
            if not unset:
                target_chain.append_rule(rule)
            else:
                target_chain.delete_rule(rule)
        except iptc.ip4tc.IPTCError as ex:
            message = "WARNING \'{}\'".format(ex)
            collect_agent.send_log(syslog.LOG_WARNING, message)

    for ip in dst_ip:
        rule = iptc.Rule()
        rule.protocol = "tcp"
        rule.dst = str(ip)
        rule.create_target("TPROXY")
        rule.target.set_parameter("on_port", str(port))
        rule.target.set_parameter("tproxy_mark", str(mark))
        try:
            if not unset:
                target_chain.append_rule(rule)
            else:
                target_chain.delete_rule(rule)
        except iptc.ip4tc.IPTCError as ex:
            message = "WARNING \'{}\'".format(ex)
            collect_agent.send_log(syslog.LOG_WARNING, message)

def main(ifaces, src_ip, dst_ip, stop, port, addr, fopen, maxconns,
         gcc_interval, log_file, pending_time, mark, table_num):
    conffile = "/opt/openbach/agent/jobs/pep/pep_rstat_filter.conf"
    collect_agent.register_collect(conffile)
    
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job pep')

    if stop:
        # unset routing configuration
        set_conf(ifaces, src_ip, dst_ip, port, mark, table_num, unset=True)
    else:
        # set routing conf
        set_conf(ifaces, src_ip, dst_ip, port, mark, table_num)
       
        # stop pepsal service
        try:
            subprocess.call(["systemctl", "stop", "pepsal.service"])
        except Exception as ex:
            collect_agent.send_log(syslog.LOG_DEBUG, "Error when stopping"
                                   " pepsal service (may be already stopped)")
        else:
            collect_agent.send_log(syslog.LOG_DEBUG, "pepsal.service stopped")
                

        # lauch pepsal
        cmd = [
                'pepsal', str(fopen), '-p', str(port),
                '-a', str(addr), '-c', str(maxconns),
                '-g', str(gcc_interval), '-l', str(log_file),
                '-t', str(pending_time)
        ]
        rc = subprocess.call(cmd)
        if rc:
            message = "WARNING \'{}\' exited with non-zero code".format(
                    ' '.join(cmd))
            collect_agent.send_log(syslog.LOG_WARNING, message)

if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(description='',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-p', '--port', type=int, default=5000,
                        help='')
    parser.add_argument('-a', '--address', type=str, default="0.0.0.0",
                        help='')
    parser.add_argument('-f', '--fastopen', action="store_true", help='')
    parser.add_argument('-c', '--maxconns', type=int, default=2112, help='')
    parser.add_argument('-g', '--gcc-interval', type=int, default=54000, help='')
    parser.add_argument('-l', '--log-file', type=str,
                        default="/var/log/pepsal/connections.log", help='')
    parser.add_argument('-t', '--pending-time', type=int, default=18000,
                        help='')
    parser.add_argument('-x', '--stop', action="store_true", help='')
    parser.add_argument('-i', '--ifaces', type=str, default='', help='')
    parser.add_argument('-s', '--src-ip', type=str, default='', help='')
    parser.add_argument('-d', '--dst-ip', type=str, default='', help='')
    parser.add_argument('-m', '--mark', type=int, default=1,
                        help='')
    parser.add_argument('-T', '--table-num', type=int, default=100,
                        help='')

    # get args
    args = parser.parse_args()
    port = args.port
    addr = args.address
    fopen = '-f' if args.fastopen else ''
    maxconns = args.maxconns
    gcc_interval = args.gcc_interval
    log_file = args.log_file
    pending_time = args.pending_time
    ifaces = args.ifaces.split(',')
    ifaces = list(filter(None, ifaces))
    src_ip = args.src_ip.split(',')
    src_ip = list(filter(None, src_ip))
    dst_ip = args.dst_ip.split(',')
    dst_ip = list(filter(None, dst_ip))
    stop = args.stop
    mark = args.mark
    table_num = args.table_num

    main(ifaces, src_ip, dst_ip, stop, port, addr, fopen, maxconns,
         gcc_interval, log_file, pending_time, mark, table_num)
