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


"""Sources of the Job squid"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Alban FRICOT <alban.fricot@toulouse.viveris.com>
'''


import time
import syslog
import argparse
import subprocess
import sys
import collect_agent
import shutil
import enum
import os.path
import socket
import iptc

CURRENT_DIRECTORY=os.path.abspath(os.path.dirname(__file__))


class Platform(enum.Enum):
    GATEWAY = 'gw'
    SATELLITE_TERMINAL = 'st'


def command_line_flag_for_argument(argument, flag):
    if argument is not None:
        yield flag
        yield str(argument)


def handle_exception(exception, timestamp):
    message = 'ERROR: {}'.format(exception)
    collect_agent.send_stat(timestamp, status=message)
    collect_agent.send_log(syslog.LOG_ERR, message)
    sys.exit(message)


def configure_platform(trans_proxy, non_transp_proxy):
    hostname=socket.gethostname()
    with open("/etc/squid/squid.conf", "a") as squid_file:
        squid_file.write("visible_hostname {}".format(hostname))
        squid_file.write("\nhttp_port {}".format(non_transp_proxy))
        squid_file.write("\nhttp_port {} intercept".format(trans_proxy))
        squid_file.write("\nhttp_port 80 vhost")
    

def main(trans_proxy, source_addr, input_iface, non_transp_proxy, path_conf_file):
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/squid/'
            'squid_rstats_filter.conf')
    if not success:
        sys.exit("Cannot connect to rstats")
    
    if path_conf_file is not None:
    # copy squid configuration file from other dir
        shutil.copy(path_conf_file, dstdir)
    else:
        srcfile = os.path.join(CURRENT_DIRECTORY, 'squid.conf')
        dstdir = '/etc/squid/'

        # Copy squid conf file
        shutil.copy(srcfile, dstdir)
 
        # set iptable rule with arguments
        table = iptc.Table(iptc.Table.NAT)
        target_chain = None
        for chain in table.chains:
            if chain.name == "PREROUTING":
                target_chain = chain
                break
        if target_chain is None:
            message = "ERROR could not find chain PREROUTING of NAT table"
            collect_agent.send_log(syslog.LOG_ERROR, message)
            sys.exit(message)

        rule = iptc.Rule()
        rule.in_interface = str(input_iface)
        rule.src = "{}/24".format(source_addr)
        rule.protocol = "tcp"
        match = rule.create_match("tcp")
        match.dport = "80"
        rule.create_target("REDIRECT")
        rule.target.set_parameter("to_ports", str(trans_proxy))
        try:
            target_chain.append_rule(rule)
        except iptc.ip4tc.IPTCError as ex:
            message = "ERROR \'{}\'".format(ex)
            collect_agent.send_log(syslog.LOG_ERROR, message)
            sys.exit(message)

        configure_platform(trans_proxy, non_transp_proxy)

    # launch squid for params
    cmd = ['squid', '-C', '-N', 'd1']
    # persitent jobs that only finishes when it is stopped by OpenBACH
    while True:
        timestamp = int(time.time() * 1000)
        try:
            output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        except subprocess.CalledProcessError as ex:
            if ex.returncode in (-15, -9):
                continue
            handle_exception(ex, timestamp)
        try:
            output = output.stdout.read()
        except IndexError as ex:
            handle_exception(ex, timestamp)
        collect_agent.send_stat(timestamp, rtt=output)


def parse_command_line():
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('non_transp_proxy', type=int,
                        help='')
    parser.add_argument('-t', '--trans_proxy', type=int,
                        help='')
    parser.add_argument('-s', '--source_addr', type=str,
                        help='')
    parser.add_argument('-i', '--input_iface', type=str,
                        help='')
    parser.add_argument('-p', '--path-conf-file', type=Platform,
                        help='')

    # get args
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_command_line()
    trans_proxy = args.trans_proxy
    source_addr = args.source_addr
    input_iface = args.input_iface
    non_transp_proxy = args.non_transp_proxy
    path_conf_file = args.path_conf_file

    print ('Argument List:', str(sys.argv))

    print (trans_proxy)
    print (source_addr)
    print (input_iface)
    print (non_transp_proxy)
    print (path_conf_file)

    main(trans_proxy, source_addr, input_iface, non_transp_proxy, path_conf_file)
