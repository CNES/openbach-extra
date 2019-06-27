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


"""Sources of the Job tcp_conf_linux"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Bastien TAURAN <bastien.tauran@viveris.com>
'''

import sys
import syslog
import argparse
import subprocess
import collect_agent

def main(reset, tcp_congestion_control, tcp_slow_start_after_idle,
    tcp_no_metrics_save,tcp_sack,tcp_recovery,tcp_wmem_min,tcp_wmem_default,
    tcp_wmem_max,tcp_fastopen,tcp_low_latency):
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/tcp_conf_linux/'
            'tcp_conf_linux_rstats_filter.conf'
    )
    collect_agent.send_log(syslog.LOG_DEBUG, "Starting job tcp_conf_linux")

    if reset:
        print("reset")
        for line in open("/opt/openbach/agent/jobs/tcp_conf_linux/60-openbach-tcp_conf_linux.conf","r"):
            name,value = line.split(" = ")
            value = value.rstrip()
            if " " in value or "\t" in value:
                value = "\""+value+"\""
            cmd = "sysctl {}={}".format(name,value)
            print(cmd)
            rc = subprocess.call(cmd, shell=True)
            if rc:
                message = "WARNING \'{}\' exited with non-zero code".format(cmd)

    changes = {}
    conf_file = open("/etc/sysctl.d/60-openbach-job.conf","w")
    if tcp_congestion_control:
        conf_file.write("net.ipv4.tcp_congestion_control="+tcp_congestion_control+"\n")
        changes["net.ipv4.tcp_congestion_control"] = tcp_congestion_control
    if tcp_slow_start_after_idle:
        conf_file.write("net.ipv4.tcp_slow_start_after_idle="+str(tcp_slow_start_after_idle)+"\n")
        changes["net.ipv4.tcp_slow_start_after_idle"] = tcp_slow_start_after_idle
    if tcp_no_metrics_save:
        conf_file.write("net.ipv4.tcp_no_metrics_save="+str(tcp_no_metrics_save)+"\n")
        changes["net.ipv4.tcp_no_metrics_save"] = tcp_no_metrics_save
    if tcp_sack:
        conf_file.write("net.ipv4.tcp_sack="+str(tcp_sack)+"\n")
        changes["net.ipv4.tcp_sack"] = tcp_sack
    if tcp_recovery:
        conf_file.write("net.ipv4.tcp_recovery="+str(tcp_recovery)+"\n")
        changes["net.ipv4.tcp_recovery"] = tcp_recovery
    if tcp_wmem_min or tcp_wmem_default or tcp_wmem_max:
        rc = subprocess.Popen("cat /proc/sys/net/ipv4/tcp_wmem", shell=True, 
            stdout=subprocess.PIPE)
        wmem_old = [x.decode("utf-8") for x in rc.stdout.read().split()]
        if not tcp_wmem_min:
            tcp_wmem_min = wmem_old[0]
        if not tcp_wmem_default:
            tcp_wmem_default = wmem_old[1]
        if not tcp_wmem_max:
            tcp_wmem_max = wmem_old[2]
        conf_file.write("net.ipv4.tcp_wmem="+str(tcp_wmem_min)+" "+
            str(tcp_wmem_default)+" "+str(tcp_wmem_max)+"\n")
        changes["net.ipv4.tcp_wmem"] = "\""+str(tcp_wmem_min)+" "+str(tcp_wmem_default)+" "+str(tcp_wmem_max)+"\""
    if tcp_fastopen:
        conf_file.write("net.ipv4.tcp_fastopen="+str(tcp_fastopen)+"\n")
        changes["net.ipv4.tcp_fastopen"] = tcp_fastopen
    if tcp_low_latency:
        conf_file.write("net.ipv4.tcp_low_latency="+str(tcp_low_latency)+"\n")
        changes["net.ipv4.tcp_low_latency"] = tcp_low_latency

    print(reset, tcp_congestion_control, tcp_slow_start_after_idle,
    tcp_no_metrics_save,tcp_sack,tcp_recovery,tcp_wmem_min,tcp_wmem_default,
    tcp_wmem_max,tcp_fastopen,tcp_low_latency)

    rc = subprocess.call("systemctl restart procps", shell=True)
    print(rc)

    print(changes)

    for name,value in changes.items():
        cmd = "sysctl {}={}".format(name,value)
        print(cmd)
        rc = subprocess.call(cmd, shell=True)
        if rc:
            message = "WARNING \'{}\' exited with non-zero code".format(cmd)

if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--reset', action='store_true', help='Resets the parameters to default configuration before applying changes')
    parser.add_argument('--tcp_congestion_control', type=str)
    parser.add_argument('--tcp_slow_start_after_idle', type=int)
    parser.add_argument('--tcp_no_metrics_save', type=int)
    parser.add_argument('--tcp_sack', type=int)
    parser.add_argument('--tcp_recovery', type=int)
    parser.add_argument('--tcp_wmem_min', type=int)
    parser.add_argument('--tcp_wmem_default', type=int)
    parser.add_argument('--tcp_wmem_max', type=int)
    parser.add_argument('--tcp_fastopen', type=int)
    parser.add_argument('--tcp_low_latency', type=int)

    # get args
    args = vars(parser.parse_args())

    print(args)

    main(**args)