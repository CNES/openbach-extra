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
import time

def set_main_args(reset, tcp_congestion_control, tcp_slow_start_after_idle,
    tcp_no_metrics_save,tcp_sack,tcp_recovery,tcp_wmem_min,tcp_wmem_default,
    tcp_wmem_max,tcp_fastopen):
    collect_agent.register_collect(
        '/opt/openbach/agent/jobs/tcp_conf_linux/'
        'tcp_conf_linux_rstats_filter.conf'
    )
    collect_agent.send_log(syslog.LOG_DEBUG, "Starting job tcp_conf_linux")

    #resets to defaults config if asked
    if reset:
        src = open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf","r")
        for line in src:
            name,value = line.split("=")
            while '.' in name:
                name = name.replace('.','/')
            dst=open("/proc/sys/"+name,"w")
            dst.write(value)
            dst.close()
        src.close()
        src = open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf","r")
        for line in src:
            name,value = line.split("=")
            value = value.rstrip()
            dst = open("/sys/module/tcp_cubic/parameters/"+name,"w")
            dst.write(value)
            dst.close()
        src.close()

    #writing changes in /etc/sysctl.d/60-openbach-job.conf
    conf_file = open("/etc/sysctl.d/60-openbach-job.conf","w")
    if tcp_congestion_control is not None:
        conf_file.write("net.ipv4.tcp_congestion_control="+tcp_congestion_control+"\n")
    if tcp_slow_start_after_idle is not None:
        conf_file.write("net.ipv4.tcp_slow_start_after_idle="+str(tcp_slow_start_after_idle)+"\n")
    if tcp_no_metrics_save is not None:
        conf_file.write("net.ipv4.tcp_no_metrics_save="+str(tcp_no_metrics_save)+"\n")
    if tcp_sack is not None:
        conf_file.write("net.ipv4.tcp_sack="+str(tcp_sack)+"\n")
    if tcp_recovery is not None:
        conf_file.write("net.ipv4.tcp_recovery="+str(tcp_recovery)+"\n")
    if tcp_wmem_min is not None or tcp_wmem_default is not None or tcp_wmem_max is not None:
        rc = subprocess.Popen("cat /proc/sys/net/ipv4/tcp_wmem", shell=True, 
            stdout=subprocess.PIPE)
        wmem_old = [x.decode("utf-8") for x in rc.stdout.read().split()]
        if tcp_wmem_min is None:
            tcp_wmem_min = wmem_old[0]
        if tcp_wmem_default is None:
            tcp_wmem_default = wmem_old[1]
        if tcp_wmem_max is None:
            tcp_wmem_max = wmem_old[2]
        conf_file.write("net.ipv4.tcp_wmem="+str(tcp_wmem_min)+" "+
            str(tcp_wmem_default)+" "+str(tcp_wmem_max)+"\n")
    if tcp_fastopen is not None:
        conf_file.write("net.ipv4.tcp_fastopen="+str(tcp_fastopen)+"\n")
    conf_file.close()

    #loading new configuration
    rc = subprocess.call("systemctl restart procps", shell=True)
    if rc:
        message = "WARNING \'{}\' exited with non-zero code".format(cmd)
        collect_agent.send_log(syslog.LOG_ERR, message)

    #retrieving new values
    statistics = {}
    for param in ["tcp_congestion_control", "tcp_slow_start_after_idle",
    "tcp_no_metrics_save", "tcp_sack", "tcp_recovery", "tcp_fastopen"]:
        file = open("/proc/sys/net/ipv4/"+param)
        statistics[param] = file.readline()
        file.close()

    file = open("/proc/sys/net/ipv4/tcp_wmem")
    new_wmem = file.readline().split()
    statistics["tcp_wmem_min"] = new_wmem[0]
    statistics["tcp_wmem_default"] = new_wmem[1]
    statistics["tcp_wmem_max"] = new_wmem[2]
    file.close()

    collect_agent.send_stat(int(time.time() * 1000), **statistics)

def cubic(reset, tcp_slow_start_after_idle,
    tcp_no_metrics_save,tcp_sack,tcp_recovery,tcp_wmem_min,tcp_wmem_default,
    tcp_wmem_max,tcp_fastopen,beta,fast_convergence,hystart_ack_delta,
    hystart_low_window,tcp_friendliness,hystart,hystart_detect,initial_ssthresh):
    set_main_args(reset, "cubic", tcp_slow_start_after_idle,
    tcp_no_metrics_save,tcp_sack,tcp_recovery,tcp_wmem_min,tcp_wmem_default,
    tcp_wmem_max,tcp_fastopen)

    # getting changes to CUBIC parameters in /etc/module/tcp_cubic/parameters and
    # writing changes in /etc/sysctl.d/60-openbach-job-cubic.conf
    changes = {}
    conf_file = open("/etc/sysctl.d/60-openbach-job-cubic.conf","w")
    if beta is not None:
        conf_file.write("net.ipv4.beta="+str(beta)+"\n")
        changes["beta"] = beta
    if fast_convergence is not None:
        conf_file.write("net.ipv4.fast_convergence="+str(fast_convergence)+"\n")
        changes["fast_convergence"] = fast_convergence
    if hystart_ack_delta is not None:
        conf_file.write("net.ipv4.hystart_ack_delta="+str(hystart_ack_delta)+"\n")
        changes["hystart_ack_delta"] = hystart_ack_delta
    if hystart_low_window is not None:
        conf_file.write("net.ipv4.hystart_low_window="+str(hystart_low_window)+"\n")
        changes["hystart_low_window"] = hystart_low_window
    if tcp_friendliness is not None:
        conf_file.write("net.ipv4.tcp_friendliness="+str(tcp_friendliness)+"\n")
        changes["tcp_friendliness"] = tcp_friendliness
    if hystart is not None:
        conf_file.write("net.ipv4.hystart="+str(hystart)+"\n")
        changes["hystart"] = hystart
    if hystart_detect is not None:
        conf_file.write("net.ipv4.hystart_detect="+str(hystart_detect)+"\n")
        changes["hystart_detect"] = hystart_detect
    if initial_ssthresh is not None:
        conf_file.write("net.ipv4.initial_ssthresh="+str(initial_ssthresh)+"\n")
        changes["initial_ssthresh"] = initial_ssthresh
    conf_file.close()

    #applying changes
    for name,value in changes.items():
        dst=open("/sys/module/tcp_cubic/parameters/"+name,"w")
        dst.write(str(value))
        dst.close()

    #retrieving new values for tcp_cubic parameters
    statistics = {}
    for param in ["beta", "fast_convergence", "hystart_ack_delta",
    "hystart_low_window", "tcp_friendliness", "hystart", "hystart_detect",
    "initial_ssthresh"]:
        file = open("/sys/module/tcp_cubic/parameters/"+param)
        statistics[param] = file.readline()
        file.close()

    collect_agent.send_stat(int(time.time() * 1000), **statistics)

def other_CC(reset, tcp_slow_start_after_idle,
    tcp_no_metrics_save,tcp_sack,tcp_recovery,tcp_wmem_min,tcp_wmem_default,
    tcp_wmem_max,tcp_fastopen,congestion_control_name):
    set_main_args(reset, congestion_control_name, tcp_slow_start_after_idle,
    tcp_no_metrics_save,tcp_sack,tcp_recovery,tcp_wmem_min,tcp_wmem_default,
    tcp_wmem_max,tcp_fastopen)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--reset', action='store_true', help='Resets the parameters to default configuration before applying changes')
    parser.add_argument('--tcp_slow_start_after_idle', type=int)
    parser.add_argument('--tcp_no_metrics_save', type=int)
    parser.add_argument('--tcp_sack', type=int)
    parser.add_argument('--tcp_recovery', type=int)
    parser.add_argument('--tcp_wmem_min', type=int)
    parser.add_argument('--tcp_wmem_default', type=int)
    parser.add_argument('--tcp_wmem_max', type=int)
    parser.add_argument('--tcp_fastopen', type=int)

    subparsers = parser.add_subparsers(
            title='Subcommand mode',
            help='Choose the congestion control')
    subparsers.required=True
    parser_cubic = subparsers.add_parser('CUBIC', help='CUBIC chosen')
    parser_cubic.add_argument('--beta', type=int)
    parser_cubic.add_argument('--fast_convergence', type=int)
    parser_cubic.add_argument('--hystart_ack_delta', type=int)
    parser_cubic.add_argument('--hystart_low_window', type=int)
    parser_cubic.add_argument('--tcp_friendliness', type=int)
    parser_cubic.add_argument('--hystart', type=int)
    parser_cubic.add_argument('--hystart_detect', type=int)
    parser_cubic.add_argument('--initial_ssthresh', type=int)

    parser_other = subparsers.add_parser('other', help='other CC chosen')
    parser_other.add_argument('congestion_control_name', type=str)

    parser_cubic.set_defaults(function=cubic)
    parser_other.set_defaults(function=other_CC)

    args = vars(parser.parse_args())

    main = args.pop('function')
    main(**args)