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


"""Sources of the Job http_server"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David PRADAS <david.pradas@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''


from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn, TCPServer
from concurrent.futures import ThreadPoolExecutor

import argparse
import os
import sys
import syslog
import collect_agent


class RandomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        os.chdir('/opt/openbach/agent/jobs/http_server')
        try:
            return SimpleHTTPRequestHandler.do_GET(self)
        except IOError as ex:
            collect_agent.send_log(
                    syslog.LOG_ERR,
                    'ERROR receiving HTTP request from client: {}'.format(ex))


class PoolMixIn(ThreadingMixIn):
    def process_request(self, request, client_address):
        self.pool.submit(self.process_request_thread, request, client_address)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True


class PoolHTTPServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True
    pool = ThreadPoolExecutor(max_workers=200)


def main(port):
    # Connect to the agent collect service
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/http_server/'
            'http_server_rstats_filter.conf')
    collect_agent.send_log(syslog.LOG_DEBUG, "Starting job http_server")

    httpd = PoolHTTPServer(('', port), RandomHTTPRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            'port', type=int,
            help='Port where the server id available')

    # get args
    args = parser.parse_args()
    main(args.port)
