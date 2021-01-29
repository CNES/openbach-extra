#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


"""Sources of the Job system_utilization"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Francklin SIMO <francklin.simo@toulouse.viveris.com>
'''

import os
import time
import psutil
import syslog
import argparse
import traceback
import contextlib
import collect_agent

@contextlib.contextmanager
def use_configuration(filepath):
    success = collect_agent.register_collect(filepath)
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job ' + os.environ.get('JOB_NAME', '!'))
    try:
        yield
    except:
        message = traceback.format_exc()
        collect_agent.send_log(syslog.LOG_CRIT, message)
        raise

def main(interval):
    while True:
        statistics= dict()
        statistics.update({'cpu_percent':psutil.cpu_percent()})
        statistics.update({'virtual_memory_percent':psutil.virtual_memory().percent})
        statistics.update({'swap_memory_percent':psutil.swap_memory().percent})
        statistics.update({'disk_space_percent':psutil.disk_usage(psutil.disk_partitions()[0].mountpoint).percent})
        timestamp = int(time.time() * 1000)
        collect_agent.send_stat(timestamp, **statistics)
        time.sleep(interval)
      
    
if __name__ == "__main__":
    with use_configuration('/opt/openbach/agent/jobs/system_utilization/system_utilization_rstats_filter.conf'):
        # Argument parsing
        parser = argparse.ArgumentParser()
        parser.add_argument('-i', '--interval', type=int, 
                            help='The pause *interval* seconds between periodic information retrieval (Default: 1 second)',
                            default=1)
                                
        args = parser.parse_args()
        main(args.interval)
        
