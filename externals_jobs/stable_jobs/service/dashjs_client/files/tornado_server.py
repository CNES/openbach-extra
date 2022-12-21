#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2023 CNES
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
import asyncio
import argparse

import collect_agent
from tornado import ioloop, web, websocket


DESCRIPTION = "This script launches a tornado server to collect statistics from dashjs_client"


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


def run_tornado(port):
    """
    Start tornado to handle websocket requests
    Args:
    Returns:
        NoneType
    """
    application = web.Application([
        (r'/websocket/', CustomWebSocket)
    ])

    listen_message = 'Starting tornado on {}:{}'.format('0.0.0.0', port)
    collect_agent.send_log(syslog.LOG_DEBUG, listen_message)
    try:
        # Add a event loop
        asyncio.set_event_loop(asyncio.new_event_loop())
        application.listen(port, '0.0.0.0')
        ioloop.IOLoop.current().start()
    except Exception as ex:
        message = 'Error when starting tornado: {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        ioloop.IOLoop.current().stop()
        sys.exit(message)


def main(port):
    # Connect to collect_agent
    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job dashjs_client')

    run_tornado(port) 


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/dashjs_client/dashjs_client_rstats_filter.conf'):
        # Define usage
        parser = argparse.ArgumentParser(
                description='',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
                '-p', '--port', type=int, default=5301,
                help='Port used by the Tornado Server to get statistics from the DASH client (Default: 5301)')

        args = parser.parse_args()
        main(args.port)
