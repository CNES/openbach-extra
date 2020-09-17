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
import json
import syslog
import argparse
import asyncio
from contextlib import suppress

import collect_agent
from tornado import ioloop, web, websocket
from tornado.options import define, options

DESCRIPTION = "This script launches a tornado server to collect statistics from dashjs_client"


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
        # filter out unwanted values and convert others to float
        data = {
            stat_name: float(stat_value) if isinstance(stat_value, str) else stat_value
            for stat_name, stat_value in data.items()
            if stat_name not in ('latency_max', 'download_max', 'ratio_max') or stat_value != 'Infinity'
        }
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

    listen_message = 'Starting tornado on {}:{}'.format('0.0.0.0', options.port)
    collect_agent.send_log(syslog.LOG_DEBUG, listen_message)
    try:
        # Add a event loop
        asyncio.set_event_loop(asyncio.new_event_loop())
        application.listen(options.port, '0.0.0.0')
        ioloop.IOLoop.current().start()
    except Exception as ex:
        message = 'Error when starting tornado: {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        ioloop.IOLoop.current().stop()
        sys.exit(message)


def main():
    # Connect to collect_agent
    connect_to_collect_agent()
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job dashjs_client')

    run_tornado() 

if __name__ == '__main__':
    # Define usage
    parser = argparse.ArgumentParser(
            description='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            '-p', '--port', type=int, default=5301,
            help='Port used by the Tornado Server to get statistics from the DASH client (Default: 5301)')

    define("port", default=parser.parse_args().port, help="port to listen on")
    main()
