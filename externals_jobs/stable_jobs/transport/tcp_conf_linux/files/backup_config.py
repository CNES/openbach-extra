#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2020 CNES
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


"""Copy the default configuration in /opt/openbach/agent/jobs/tcp_conf_linux/
at job installation"""

import os.path
from glob import glob

# Backup generic TCP stack parameters
dst = open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf","w")
for param in [
        "tcp_congestion_control", "tcp_slow_start_after_idle", 
        "tcp_no_metrics_save", "tcp_sack", "tcp_recovery", "tcp_wmem",
        "tcp_rmem", "tcp_fastopen"]:
    src = open("/proc/sys/net/ipv4/"+param,"r")
    value = src.readline()
    src.close()
    dst.write("net.ipv4."+param+"="+value)

for param in ["rmem_max", "rmem_default", "wmem_max", "wmem_default"]:
    src = open("/proc/sys/net/core/"+param,"r")
    value = src.readline()
    src.close()
    dst.write("net.core."+param+"="+value)

dst.close()

# Get current name of "hystart_ack_delta" parameter since it can be different
# according to the Linux kernel
hystart_ack_delta = list(map(
        os.path.basename,
        glob("/sys/module/tcp_cubic/parameters/hystart_ack_delta*")))[0]

# Backup parameters of TCP CUBIC protocol
dst = open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf","w")
for param in [
        "beta", "fast_convergence", hystart_ack_delta, "hystart_low_window",
        "tcp_friendliness", "hystart", "hystart_detect", "initial_ssthresh"]:
    src = open("/sys/module/tcp_cubic/parameters/"+param,"r")
    value = src.readline()
    src.close()
    dst.write(param+"="+value)

dst.close()
