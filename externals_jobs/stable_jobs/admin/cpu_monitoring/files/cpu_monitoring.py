#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016−2023 CNES
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


"""Sources of the Job cpu_monitoring"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Bastien TAURAN <bastien.tauran@viveris.fr>
 * David FERNANDES <david.fernandes@viveris.fr>
'''


import re
import syslog
import argparse
import subprocess
from threading import Thread
from apscheduler.schedulers.blocking import BlockingScheduler

import collect_agent


def cpu_reports(sampling_interval):
    cmd = ['stdbuf', '-oL', 'mpstat', '-P', 'ALL', str(sampling_interval)]
    p = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE)

    p.stdout.readline()  # Skip header
    while line := p.stdout.readline():
        try:
            _, core, cpu_user, _, cpu_sys, cpu_iowait, _, _, _, _, _, cpu_idle = line.split()
        except ValueError:
            pass
        else:
            if core == 'CPU':
                timestamp = collect_agent.now()
            else:
                cpu_index = None if core == 'all' else int(core)
                collect_agent.send_stat(
                        timestamp, suffix=cpu_index,
                        cpu_user=float(cpu_user),
                        cpu_sys=float(cpu_sys),
                        cpu_iowait=float(cpu_iowait),
                        cpu_idle=float(cpu_idle))


def mem_report():
    timestamp = collect_agent.now()
    cmd = ['stdbuf', '-oL', 'free', '-b']
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE)

    p.stdout.readline()  # Skip header
    ram_used = int(p.stdout.readline().split()[2])
    swap_used = int(p.stdout.readline().split()[2])
    collect_agent.send_stat(timestamp, ram_used=ram_used, swap_used=swap_used)


def command_line_parser():
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            '--sampling-interval', '-i',
            type=int, default=1,
            help='interval between two measurements in seconds')
    return parser


def main(sampling_interval):
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting cpu_monitoring job')

    # Collect CPU reports
    thread = Thread(target=cpu_reports, args=(sampling_interval,))
    thread.start()

    # Collect memory reports
    sched = BlockingScheduler()
    sched.add_job(mem_report, 'interval', seconds=sampling_interval)
    sched.start()

    thread.join()


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/cpu_monitoring/cpu_monitoring_rstats_filter.conf'):
        args = command_line_parser().parse_args()
        main(**vars(args))
