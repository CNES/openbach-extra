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


"""Call the openbach-function add_collector"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import getpass
from functools import partial

from frontend import FrontendBase


class AddCollector(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Add Collector')
        self.parser.add_argument(
                'collector',
                help='IP address of the collector')
        self.parser.add_argument(
                'name',
                help='name of the agent installed on the collector')
        self.parser.add_argument(
                '-l', '--logs-port', type=int,
                help='port for the logs')
        self.parser.add_argument(
                '-s', '--stats-port', type=int,
                help='port for the stats')
        self.parser.add_argument(
                '-u', '--user',
                help='username to connect as on the collector-to-be '
                'if the SSH key of the controller cannot be used to '
                'connect to the openbach user on the machine.')

    def parse(self, args=None):
        super().parse(args)
        username = self.args.user
        password = None
        if username is not None:
            address = self.args.collector
            prompt = 'Password for {} on {}: '.format(username, address)
            password = getpass.getpass(prompt)
        self.args.password = password

    def execute(self, show_response_content=True):
        collector = self.args.collector
        name = self.args.name
        logs_port = self.args.logs_port
        stats_port = self.args.stats_port
        username = self.args.user
        password = self.args.password

        action = self.request
        if logs_port is not None:
            action = partial(action, logs_port=logs_port)
        if stats_port is not None:
            action = partial(action, stats_port=stats_port)
        action('POST', 'collector', show_response_content=False,
               username=username, password=password,
               address=collector, name=name)
        self.wait_for_success('add', show_response_content)

    def query_state(self):
        address = self.args.collector
        return self.request(
                'GET', 'collector/{}/state/'.format(address),
                show_response_content=False)


if __name__ == '__main__':
    AddCollector.autorun()
