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


BRACKETS = re.compile(r'[\[\]]')


def cpu_reports(sampling_interval):
    cmd = ['stdbuf', '-oL', 'mpstat', str(sampling_interval)]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    while True:
        line = p.stdout.readline().decode()
        tokens = BRACKETS.sub('', line).split()
        if not tokens:
            if p.poll() is not None:
                break
            continue
        line = line.strip()
        if 'all' in line:
            elts = line.split()
            o = elts.index('all')
            cpu_user, cpu_sys, cpu_iowait, cpu_idle = map(float, [elts[o + 1], elts[o + 3], elts[o + 4], elts[o + 10]])
            statistics = {}
            timestamp = collect_agent.now()
            statistics['cpu_user'] = cpu_user
            statistics['cpu_sys'] = cpu_sys
            statistics['cpu_iowait'] = cpu_iowait
            statistics['cpu_idle'] = cpu_idle
            collect_agent.send_stat(timestamp, **statistics)


def mem_report():
    statistics = {}
    timestamp = collect_agent.now()

    cmd = ['stdbuf', '-oL', 'free', '-b']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.decode().strip()
        if 'Mem:' in line:
            ram_used = int(line.split()[2])
            statistics['ram_used'] = ram_used
        if 'Swap:' in line:
            swap_used = int(line.split()[2])
            statistics['swap_used'] = swap_used

    collect_agent.send_stat(timestamp, **statistics)


def main(sampling_interval):
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting cpu_monitoring job')

    # Collect CPU reports
    thread = Thread(target=cpu_reports, args=(sampling_interval, ))
    thread.start()

    # Collect memory reports
    sched = BlockingScheduler()
    sched.add_job(
            mem_report, 'interval',
            seconds=sampling_interval)
    sched.start()

    thread.join()


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/cpu_monitoring/cpu_monitoring_rstats_filter.conf'):
        # Define Usage
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
                '--sampling-interval', '-i',
                type=int, default=1,
                help='Interval between two measurements in seconds')

        args = vars(parser.parse_args())
        main(**args)
