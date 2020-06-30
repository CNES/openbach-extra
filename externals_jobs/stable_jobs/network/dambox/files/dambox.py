#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2020 CNES
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


"""Sources of the Job dambox"""

__author__ = 'Silicom'
__credits__ = '''Contributors:
 * Corentin Ormiere  <cormiere@silicom.fr>
'''

import argparse
import subprocess
import syslog
import collect_agent
from statistics import mean
import time
import sys
import iptc

#Path for timeline file and debbug file
path_conf="/home/openbach/"

def command_line_flag_for_argument(argument, flag):
    if argument is not None:
        yield flag
        yield str(argument)


def createFileTimeline(timeline):
    f = open(path_conf + "timeline.txt", "w+")
    f.write(timeline + '\n')
    f.close()

def createFilecmd(cmd):
    f = open(path_conf + "cmd.txt", "w+")
    f.write(cmd + '\n')
    f.close()


def main(beamslot, mode, value_mode,iface, duration, simultaneous_verdict):

    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/dambox/dambox_rstats_filter.conf')
    if not success:
        message = "ERROR connecting to collect-agent"
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job dambox')

    #Flush Iptables
    rule = " -F"
    list_rule = rule.split()
    cmd = ["iptables"] + list_rule
    print(cmd)
    try:
        p = subprocess.run(cmd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as ex:
        collect_agent.send_log(syslog.LOG_ERR, "Error when executing command {}: {}".format(cmd, ex))
    if p.returncode:
        message = 'WARNING: {} exited with non-zero return value ({}): {}'.format(cmd, p.returncode, p.stderr.decode())
        collect_agent.send_log(syslog.LOG_WARNING, message)
        sys.exit(0)

    #equiavlent of "iptables -I FORWARD -o ensXXX -j NFQUEUE"
    rule = iptc.Rule()
    rule.target = iptc.Target(rule, "NFQUEUE")
    rule.in_interface = str(iface)
    chain = iptc.Chain(iptc.Table(iptc.Table.FILTER), "FORWARD")
    #chain.insert_rule(rule)
    try:
            chain.insert_rule(rule)

    except iptc.ip4tc.IPTCError as ex:
        message = "WARNING \'{}\'".format(ex)
        collect_agent.send_log(syslog.LOG_WARNING, message)




    cmd = ["dambox"]
    cmd.extend(command_line_flag_for_argument(damslot*1000, "-bs")) 
    #Check between frequency or timeline mode
    if mode=="timeline":
        # Create and put the timeline (ex 1000101) in a file for the BH binary
        createFileTimeline(value_mode)
        cmd.extend(command_line_flag_for_argument(path_conf+ "timeline.txt", "-t"))
    elif mode=="frequency":
        cmd.extend(command_line_flag_for_argument(value_mode, "-f"))
    cmd.extend(command_line_flag_for_argument(simultaneous_verdict, "-s"))
    cmd.extend(command_line_flag_for_argument(duration, "-d"))
    createFilecmd(str(cmd))

#Launch of the bh box
    fileName = path_conf + "logfile.txt"
    with open(fileName, "w+") as f:
        rc = subprocess.call(command, shell=True, universal_newlines=True, stdout=f)
    if rc:
        message = "WARNING \'{}\' exited with non-zero code".format(
                ' '.join(cmd))
        collect_agent.send_log(syslog.LOG_WARNING, message)

#Flush Iptables
    rule = " -F"
    list_rule = rule.split()
    cmd = ["iptables"] + list_rule
    print(cmd)
    try:
        p = subprocess.run(cmd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as ex:
        collect_agent.send_log(syslog.LOG_ERR, "Error when executing command {}: {}".format(cmd, ex))
    if p.returncode:
        message = 'WARNING: {} exited with non-zero return value ({}): {}'.format(cmd, p.returncode, p.stderr.decode())
        collect_agent.send_log(syslog.LOG_WARNING, message)
        sys.exit(0)

if __name__ == '__main__':
    # define Usage
    parser = argparse.ArgumentParser(
        description='', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('damslot',help='', type=int)
    # The chosen mode, the variable contain either "frequency" or "timeline"
    parser.add_argument('mode', help='')
    # The data related to the chosen mode, 010101 for timeline, a int for freqeuncy
    parser.add_argument('value_mode', help='')
    parser.add_argument('iface', help='')
    
    # Optionnal argument
    parser.add_argument('-d', '--duration', type=int)
    parser.add_argument('-s', '--simultaneous_verdict', type=int)
    

    args = parser.parse_args()
    damslot = args.damslot
    mode = args.mode
    value_mode = args.value_mode
    duration = args.duration
    simultaneous_verdict = args.simultaneous_verdict
    iface=args.iface


main(damslot, mode, value_mode, iface,  duration, simultaneous_verdict)

