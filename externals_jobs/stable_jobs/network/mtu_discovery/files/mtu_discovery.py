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


"""Sources of the Job mtu_discovery"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David FERNANDES <david.fernandes@viveris.fr>
'''

import re
import sys
import syslog
import argparse
import subprocess

import collect_agent


def send_and_parse_icmp(ip, payload_size):
    cmd = ['ping', ip, '-c', '100', '-i', '0.01', '-M', 'do', '-W', '2', '-s', str(payload_size)]
    cmd_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = cmd_result.stdout.decode().replace('\n','')
    pattern = re.compile(r'.*{}\((\d+)\) bytes.*100 packets transmitted, (\d+) received.*'.format(payload_size))
    match = re.match(pattern, output)
    if match is None:
        message = 'Unrecognised ping output: {}'.format(output)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    return map(int, match.groups()) 
   

def main(destination_ip):
    r = [1, 10000] # Boundaries for the MTU research
    header_size = None
    sent_code = None
    payload_size = None

    while r[1] - r[0] > 0 :
        payload_size = r[1] if r[1] - r[0] == 1 else r[0] + int((r[1] - r[0]) /2)
        packet_size, sent_code = send_and_parse_icmp(destination_ip, payload_size)
        header_size = packet_size - payload_size
        if sent_code == 0:
            r[1] = payload_size - 1
        else:
            r[0] = payload_size

    if r[0] == 1:
        message = 'Calculated MTU is too low. An error may occurred.'
        collect_agent.send_log(syslog.LOG_WARNING, message)
        print(message)

    mtu = r[0] + header_size
    timestamp = collect_agent.now()
    collect_agent.send_stat(timestamp, mtu=mtu)
    print('Path MTU : {} bytes'.format(mtu))
    

if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/mtu_discovery/mtu_discovery_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('destination_ip', help='Destinaton (IP or domain)')
    
        args = parser.parse_args()
        main(args.destination_ip)
