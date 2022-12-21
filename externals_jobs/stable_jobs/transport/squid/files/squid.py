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


import os
import sys
import enum
import shutil
import syslog
import socket
import argparse
import subprocess

os.environ['XTABLES_LIBDIR'] = '$XTABLES_LIBDIR:/usr/lib/x86_64-linux-gnu/xtables' # Required for Ubuntu 20.04
import iptc

import collect_agent


CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))


class Platform(enum.Enum):
    GATEWAY = 'gw'
    SATELLITE_TERMINAL = 'st'


def configure_platform(trans_proxy, non_transp_proxy):
    hostname = socket.gethostname()
    with open("/etc/squid/squid.conf", "a") as squid_file:
        squid_file.write("visible_hostname {}".format(hostname))
        squid_file.write("\nhttp_port {}".format(non_transp_proxy))
        squid_file.write("\nhttp_port {} intercept".format(trans_proxy))
        squid_file.write("\nhttp_port 80 vhost")


def remove_squid_cache():
    shutil.rmtree('/etc/squid/cache', ignore_errors=False)
    try:
        os.makedirs('/etc/squid/cache')
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    try:
        subprocess.run(['chmod', '777', '/etc/squid/cache'], check=True, stderr=subprocess.PIPE) 
    except subprocess.CalledProcessError as error:
        if error.returncode not in (-15, -9):
            message = 'ERROR ({}):\n{}'.format(error.returncode, error.stderr.decode(errors='replace'))
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)
    try:
        subprocess.run(['squid', '-z'], check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        if error.returncode not in (-15, -9):
            message = 'ERROR ({}):\n{}'.format(error.returncode, error.stderr.decode(errors='replace'))
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)


def main(trans_proxy, source_addr, input_iface, non_transp_proxy, path_conf_file, clean_cache):
    if path_conf_file is None:
        path_conf_file = os.path.join(CURRENT_DIRECTORY, 'squid.conf')

    # Copy squid conf file
    shutil.copy(path_conf_file, '/etc/squid/squid.conf')

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

    if clean_cache:
        remove_squid_cache()

    # launch squid for params
    try:
        subprocess.run(['squid', '-N', '-C', '-d1'], check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        if error.returncode not in (-15, -9):
            message = 'ERROR ({}):\n{}'.format(error.returncode, error.stderr.decode(errors='replace'))
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)
        

def command_line_parser():
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            'non_transp_proxy', type=int,
            help='')
    parser.add_argument(
            '-t', '--trans_proxy', type=int,
            help='')
    parser.add_argument(
            '-s', '--source_addr',
            help='')
    parser.add_argument(
            '-i', '--input_iface',
            help='')
    parser.add_argument(
            '-c', '--clean_cache',
            action='store_true',
            help='Remove cache dir')
    parser.add_argument(
            '-p', '--path-conf-file',
            type=Platform,
            help='')

    return parser


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/squid/squid_rstats_filter.conf'):
        args = command_line_parser().parse_args()
        main(**vars(args))
