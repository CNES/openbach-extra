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


"""Sources of the Job mptcp"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David PRADAS <david.pradas@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''


import syslog
import argparse
import subprocess
from sys import exit

import collect_agent


SCHEDULERS = {'default', 'roundrobin', 'redundant'}
PATH_MANAGERS = {'default', 'fullmesh', 'ndiffports', 'binder'}


def exit_with_message(message):
    collect_agent.send_log(syslog.LOG_ERR, message)
    exit(message)


def sysctl_command(command, debug_log):
    try:
        subprocess.call(['sysctl', '-w', command])
        subprocess.call(['sysctl', '-p'])
        collect_agent.send_log(syslog.LOG_DEBUG, debug_log)
    except Exception as ex:
        collect_agent.send_log(
                syslog.LOG_WARNING,
                'ERROR modifying sysctl {}'.format(ex))


def main(ifaces, enable, checksum, syn_retries, path_manager, scheduler):
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/mptcp/'
            'mptcp_rstats_filter.conf')

    collect_agent.send_log(syslog.LOG_DEBUG, "Starting job mptcp")

    # Check if valid scheduler and path_manager values
    if path_manager and (path_manager not in PATH_MANAGERS):
        exit_with_message('ERROR path manager not in {}'.format(PATH_MANAGERS))
    if scheduler and (scheduler not in SCHEDULERS):
        exit_with_message('ERROR scheduler not in {}'.format(SCHEDULERS))

    # Configure MPTCP routing
    mptcp_enabled = 1 if enable else 0
    debug_message = 'enabled' if enable else 'disabled'
    sysctl_command(
            'net.mptcp.mptcp_enabled={}'.format(mptcp_enabled),
            'MPTCP is {}'.format(debug_message))

    # Change checksum
    if checksum is not None:
        sysctl_command(
                'net.mptcp.mptcp_checksum={}'.format(checksum),
                'MPTCP checksum updated')

    # Change syn_retries
    if syn_retries is not None:
        sysctl_command(
                'net.mptcp.mptcp_syn_retries={}'.format(syn_retries),
                'MPTCP syn_retries updated')

    # Change path_manager
    if path_manager is not None:
        sysctl_command(
                'net.mptcp.mptcp_path_manager={}'.format(path_manager),
                'MPTCP path_manager updated')

    # Change scheduler
    if scheduler is not None:
        sysctl_command(
                'net.mptcp.mptcp_scheduler={}'.format(scheduler),
                'MPTCP scheduler updated')

    # Get list of all interfaces
    all_ifaces = subprocess.check_output("netstat -i | awk '{print $1}' | tail"
                                         " -n +3",
                                     shell=True).decode().splitlines()
    enabled_ifaces = ifaces.split(',')
    if len(enabled_ifaces) == 0:
        enabled_ifaces = all_ifaces
    # Enable interfaces
    for iface in enabled_ifaces:
        try:
            subprocess.call(["ip", "link", "set", "dev", iface, "multipath",
                             "on"])
        except Exception as ex:
            collect_agent.send_log(
                    syslog.LOG_ERROR,
                    'Error when setting  multipath on interface {}: {}'
                    .format(iface, ex))
        else:
            collect_agent.send_log(
                    syslog.LOG_ERROR,
                    'Enabled multipath on interface {}'
                    .format(iface))
    # Disable the rest of the interfaces
    for iface in [i for i in all_ifaces if i not in enabled_ifaces]:
        try:
            subprocess.call(["ip", "link", "set", "dev", iface, "multipath",
                             "off"])
        except Exception as ex:
            collect_agent.send_log(
                    syslog.LOG_ERROR,
                    'Error when disabling  multipath on interface {}: {}'
                    .format(iface, ex))
        else:
            collect_agent.send_log(
                    syslog.LOG_ERROR,
                    'Disabled multipath on interface {}'
                    .format(iface))
            

if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--ifaces', type=str, help='')
    parser.add_argument('-e', '--enable', action='store_true')
    parser.add_argument('-k', '--checksum', type=int, help='')
    parser.add_argument('-y', '--syn-retries', type=int, help='')
    parser.add_argument('-p', '--path-manager', type=str, help='')
    parser.add_argument('-s', '--scheduler', type=str, help='')

    # get args
    args = parser.parse_args()
    ifaces = args.ifaces
    enable = args.enable
    checksum = args.checksum
    syn_retries = args.syn_retries
    path_manager = args.path_manager
    scheduler = args.scheduler
    
    main(ifaces, enable, checksum, syn_retries, path_manager, scheduler) 
