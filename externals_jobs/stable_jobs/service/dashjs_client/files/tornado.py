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


"""Source file to launch a tornado server"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Bastien TAURAN <bastien.tauran@viveris.com>
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

from tornado import ioloop, web, websocket, define, options

# Values of following variables *_PORT must be identical to those 
# specified in un/installation files of the job, so don't change

HTTP_PORT = 8083
HTT2_PORT = 8084
WS_PORT = 8085 

DESCRIPTION = ("This script launches a tornado server to collect statistics").format(HTTP_PORT, HTT2_PORT)


def connect_to_collect_agent():
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/dashjs_client/'
            'dashjs_client_rstats_filter.conf')
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


def main():
    # Connect to collect_agent
    connect_to_collect_agent()
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job dashjs_client')
    try:
        # Start tornado
        run_tornado()
    except Exception as ex:
        message = 'An unexpected error occured: {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERROR, message)
        exit(message) 

if __name__ == '__main__':
    define("port", default=5301, help="port to listen on")
    main()
