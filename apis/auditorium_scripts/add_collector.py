#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


"""Call the openbach-function add_collector"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import getpass
from functools import partial

from auditorium_scripts.frontend import FrontendBase


class AddCollector(FrontendBase):
    PASSWORD_SENTINEL = object()

    def __init__(self):
        super().__init__('OpenBACH — Add a new Collector and corresponding agent')
        self.parser.add_argument(
                'collector_address',
                help='IP address of the collector')
        self.parser.add_argument(
                'agent_name',
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
        self.parser.add_argument(
                '-p', '--passwd', '--agent-password',
                dest='agent_password', nargs='?', const=self.PASSWORD_SENTINEL,
                help='password to log into the machine for the installation '
                'process. if the flag is used without a value, an echoless '
                'prompt will ask for it; if the flag is omitted, the controller '
                'will only be able to rely on its SSH keys instead.')

    def parse(self, args=None):
        args = super().parse(args)
        if args.agent_password is self.PASSWORD_SENTINEL:
            address = args.collector_address
            prompt = 'Password for {} on {}: '.format(args.user, address)
            password = getpass.getpass(prompt)
            self.args.agent_password = password

    def execute(self, show_response_content=True):
        collector = self.args.collector_address
        agent_name = self.args.agent_name
        logs_port = self.args.logs_port
        stats_port = self.args.stats_port
        username = self.args.user
        password = self.args.agent_password

        action = self.request
        if logs_port is not None:
            action = partial(action, logs_port=logs_port)
        if stats_port is not None:
            action = partial(action, stats_port=stats_port)
        action('POST', 'collector', show_response_content=False,
               username=username, password=password,
               address=collector, name=agent_name)
        return self.wait_for_success('add', show_response_content=show_response_content)

    def query_state(self):
        address = self.args.collector_address
        return self.request(
                'GET', 'collector/{}/state/'.format(address),
                show_response_content=False)


if __name__ == '__main__':
    AddCollector.autorun()
