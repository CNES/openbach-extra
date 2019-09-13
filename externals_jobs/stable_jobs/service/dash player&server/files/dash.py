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


"""Sources of the Job dash"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
 * Mathias ETTTINGER <mettinger@toulouse.viveris.com>
 * David PRADAS <david.pradas@toulouse.viveris.com>
 * Francklin SIMO <francklin.simo@viveris.fr>
'''


import sys
import os
import json
import time
import syslog
import argparse
import subprocess
import time
import threading
import asyncio
from contextlib import suppress
import signal
from functools import partial
import psutil

import collect_agent

from tornado import ioloop, web, websocket

# Values of following variables *_PORT must be identical to those 
# specified in un/installation files of the job, so don't change

HTTP_PORT = 8083
HTT2_PORT = 8084
WS_PORT = 8085 

DESCRIPTION = ("This job launchs apache2 web server to stream on-demand a DASH "  
               "video in 4 different qualities over http/1.1 or http/2 on ports {}" 
               "and {} respectively").format(HTTP_PORT, HTT2_PORT)


def connect_to_collect_agent():
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/dash_player_server/'
            'dash player&server_rstats_filter.conf')
    if not success:
        message = 'Error connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

class CustomWebSocket(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True
        
    def open(self):
        self.set_nodelay(True)
        collect_agent.send_log(syslog.LOG_DEBUG, 'Opened websocket with IP {}'.format(self.request.remote_ip))

    def on_message(self, message):
        data = json.loads(message)

        for stat in ('latency_max', 'download_max', 'ratio_max'):
            with suppress(KeyError):
                if data[stat] == 'Infinity':
                    del data[stat]
        data['suffix'] = self.request.headers['X-Forwarded-For']
        collect_agent.send_stat(**data)
        collect_agent.send_log(syslog.LOG_DEBUG, 'Message received')

def run_tornado():
    """
    Start tornado to handle websocket requests
    Args:
    Returns:
        NoneType
    """
    application = web.Application([
        (r'/websocket/', CustomWebSocket)
    ])

    listen_message = 'Starting tornado on {}:{}'.format('0.0.0.0', WS_PORT)
    collect_agent.send_log(syslog.LOG_DEBUG, listen_message)
    try:
      # Add a event loop
      asyncio.set_event_loop(asyncio.new_event_loop())
      application.listen(WS_PORT, '0.0.0.0')
      ioloop.IOLoop.current().start()
    except Exception as ex:
       message = 'Error when starting tornado: {}'.format(ex)
       print(message)
       collect_agent.send_log(syslog.LOG_ERR, message)
       sys.exit(message)


def run_apache2():
    """
    Start apache2 to handle HTTP requests
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
    # Wait for status to change to active
    status = 0
    while (status == 0):
       time.sleep(5)
       status = os.system('systemctl is-active --quiet apache2')


def stop_apache2(signalNumber, frame):
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


def main():
    # Connect to collect_agent
    connect_to_collect_agent()
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job dash')
    try:
       # Start tornado
       th_tornado = threading.Thread(target=run_tornado, args=())
       th_tornado.start()
       # Start apache2
       th_apache2 = threading.Thread(target=run_apache2, args=())
       th_apache2.start()
       # Set signal handler
       signal.signal(signal.SIGTERM, stop_apache2)
       signal.signal(signal.SIGINT, stop_apache2)
       # Wait for threads to finish
       th_tornado.join()
       th_apache2.join()
    except Exception as ex:
       message = 'An unexpected error occured: {}'.format(ex)
       collect_agent.send_log(syslog.LOG_ERROR, message)
       exit(message) 


if __name__ == '__main__':
    # Define Usage
    parser = argparse.ArgumentParser(
            description=DESCRIPTION,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    main()
