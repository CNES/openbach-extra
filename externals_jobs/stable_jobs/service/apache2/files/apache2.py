#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2018 CNES
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


"""Sources of the Job apache2"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Francklin SIMO <francklin.simo@viveris.fr>
'''

import collect_agent
import syslog
import os
import sys
import argparse
import subprocess
import time
import signal
from functools import partial
import psutil


HTTP_PORT = 8081
HTT2_PORT = 8082

DESCRIPTION = ("This job launchs the web server apache2 that provides " 
               "HTTP services in standard http/1.1 and http2 on ports {} and {} "
               "respectively").format(HTTP_PORT, HTT2_PORT)


def connect_to_collect_agent():
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/apache2/'
            'apache2_rstats_filter.conf')
    if not success:
        message = 'Error connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


def stop(signalNumber, frame):
    """
    Stop apache2
    Args: 
    Returns:
       NoneType
    """
    connect_to_collect_agent()
    cmd = ["systemctl", "stop", "apache2"]
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when stopping apache2: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    
def start():
    """
    Start apache2 which will listen http/1.1 requests on port 8081 and http2 on port 8082
    Args:
    Returns:
        NoneType
    """
    connect_to_collect_agent()
    cmd = ["systemctl", "start", "apache2"]
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when starting apache2: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    
    # Set signal handler
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    # Wait for status to change to active
    status = 0
    while (status == 0):
        time.sleep(5)
        status = os.system('systemctl is-active --quiet apache2')



if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description=DESCRIPTION, 
                 formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
     
    start() 
