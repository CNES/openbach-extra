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
'''


import sys
import json
import time
import syslog
import argparse
from contextlib import suppress

import collect_agent

from tornado import ioloop, web, websocket


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
        
        data['suffix'] = self.request.remote_ip
        print(data["bitrate"])
        print(self.request.remote_ip)
        collect_agent.send_stat(**data)
        collect_agent.send_log(syslog.LOG_DEBUG, 'Message received')


def main(port):
    # Connect to collect_agent
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/dash_player_server/'
            'dash player&server_rstats_filter.conf')
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job dash')

    application = web.Application([
        (r'/websocket/', CustomWebSocket),
        (r'/(.*)', web.StaticFileHandler, {
            'path': '/opt/openbach/agent/jobs/dash_player_server/www/',
            'default_filename': 'index.html',
        }),
    ])

    listen_message = 'Starting tornado on {}:{}'.format('0.0.0.0', port)
    print(listen_message)
    collect_agent.send_log(syslog.LOG_DEBUG, listen_message)
    application.listen(port, '0.0.0.0')
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            '-p', '--port', type=int, default=80,
            help='Port to use to serve HTTP')

    # get args
    args = parser.parse_args()

    main(**vars(args))
