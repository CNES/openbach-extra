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


import os
import sys
import shlex
import syslog
import pathlib
import argparse
import subprocess

os.environ['XTABLES_LIBDIR'] = '$XTABLES_LIBDIR:/usr/lib/x86_64-linux-gnu/xtables' # Required for Ubuntu 20.04
import iptc

import collect_agent


PATH_CONF = pathlib.Path.home()


def command_line_flag_for_argument(argument, flag):
    if argument is not None:
        yield flag
        yield str(argument)


def flush_iptables(rule='-F'):
    cmd = ['iptables'] + shlex.split(rule)
    try:
        p = subprocess.run(cmd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as ex:
        collect_agent.send_log(syslog.LOG_ERR, 'Error when executing command {}: {}'.format(cmd, ex))
    if p.returncode:
        message = 'WARNING: {} exited with non-zero return value ({}): {}'.format(cmd, p.returncode, p.stderr.decode())
        collect_agent.send_log(syslog.LOG_WARNING, message)
        sys.exit(message)

def main(beamslot, mode, value_mode, iface, duration, simultaneous_verdict):
    flush_iptables()
    # equiavlent of "iptables -I FORWARD -o ensXXX -j NFQUEUE"
    rule = iptc.Rule()
    rule.target = iptc.Target(rule, "NFQUEUE")
    rule.in_interface = str(iface)
    chain = iptc.Chain(iptc.Table(iptc.Table.FILTER), "FORWARD")
    try:
        chain.insert_rule(rule)
    except iptc.ip4tc.IPTCError as ex:
        message = "WARNING \'{}\'".format(ex)
        collect_agent.send_log(syslog.LOG_WARNING, message)

    cmd = ["dambox"]
    cmd.extend(command_line_flag_for_argument(damslot*1000, "-ds")) 
    # Check between frequency or timeline mode
    if mode == "timeline":
        # Create and put the timeline (ex 1000101) in a file for the BH binary
        timeline_file = PATH_CONF.joinpath('timeline.txt')
        timeline_file.write_text(value_mode)
        cmd.extend(command_line_flag_for_argument(str(timeline_file), "-t"))
    elif mode == "frequency":
        cmd.extend(command_line_flag_for_argument(value_mode, "-f"))
    cmd.extend(command_line_flag_for_argument(simultaneous_verdict, "-s"))
    cmd.extend(command_line_flag_for_argument(duration, "-d"))
    PATH_CONF.joinpath('cmd.txt').write_text(str(cmd))

    # Launch of the bh box
    with PATH_CONF.joinpath('logfile.txt').open('w+') as f:
        process = subprocess.run(cmd, universal_newlines=True, stdout=f)
    if process.returncode:
        message = "WARNING \'{}\' exited with non-zero code".format(' '.join(cmd))
        collect_agent.send_log(syslog.LOG_WARNING, message)

    flush_iptables()


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/dambox/dambox_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
            description='', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('damslot', type=int, help='')
        parser.add_argument('iface', help='')
    
        # Optionnal argument
        parser.add_argument('-d', '--duration', type=int)
        parser.add_argument('-s', '--simultaneous_verdict', type=int)
    
        # Mode selection
        sub_parser = parser.add_subparsers(dest='mode')
        sub_parser.required = True
        frequency = sub_parser.add_parser('frequency')
        frequency.add_argument('value_mode', type=int, help='')
        timeline = sub_parser.add_parser('timeline')
        timeline.add_argument('value_mode', help='')
        
        args = parser.parse_args()
        damslot = args.damslot
        mode = args.mode
        value_mode = args.value_mode
        duration = args.duration
        simultaneous_verdict = args.simultaneous_verdict
        iface = args.iface
    
        main(damslot, mode, value_mode, iface,  duration, simultaneous_verdict)
