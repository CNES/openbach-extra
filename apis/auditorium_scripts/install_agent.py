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


"""Call the openbach-function install_agent"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import getpass
from argparse import FileType

from auditorium_scripts.frontend import FrontendBase


class InstallAgent(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Install Agent')
        self.parser.add_argument(
                'agent_address',
                help='IP address of the agent')
        self.parser.add_argument(
                'collector_address',
                help='IP address of the collector')
        self.parser.add_argument(
                'agent_name',
                help='name of the agent')
        self.parser.add_argument(
                '-u', '--user',
                help='username to connect as on the agent-to-be '
                'if the SSH key of the controller cannot be used to '
                'connect to the openbach user on the machine.')
        self.parser.add_argument(
                '--private_key_file', type=FileType('r'),
                help='path of private key file on the current computer to be sent to the controller')
        self.parser.add_argument(
                '--public_key_file', type=FileType('r'),
                help='path of public key file on the current computer to be sent to the controller')
        self.parser.add_argument(
                 '--http_proxy',
                help='http proxy variable for this agent')
        self.parser.add_argument(
                '--https_proxy',
                help='https proxy variable for this agent')
        self.parser.add_argument(
                '-r', '--reattach', '--attach-autonomous-agent',
                action='store_true',
                help='re-attach an existing (autonomous) agent '
                'instead of performing a full-blown installation.')

    def parse(self, args=None):
        super().parse(args)
        username = self.args.user
        password = None
        if username is not None:
            address = self.args.agent_address
            prompt = 'Password for {} on {}: '.format(username, address)
            password = getpass.getpass(prompt)
        self.args.password = password

    def execute(self, show_response_content=True):
        proxy = self.args.http_proxy
        request_data = {
                'address': self.args.agent_address,
                'name': self.args.agent_name,
                'username': self.args.user,
                'password': self.args.password,
                'collector_ip': self.args.collector_address,
                'http_proxy': proxy,
                'https_proxy': self.args.https_proxy or proxy,
        }

        private_key_file = self.args.private_key_file
        public_key_file = self.args.public_key_file
        if private_key_file and public_key_file:
            request_data['files'] = {
                    'private_file': private_key_file,
                    'public_file': public_key_file,
            }

        route = 'agent?reattach' if self.args.reattach else 'agent'
        request = self.request('POST', route, show_response_content=False, **request_data)
        request.raise_for_status()
        return self.wait_for_success('install', show_response_content=show_response_content)

    def query_state(self):
        address = self.args.agent_address
        return self.request(
                'GET', 'agent/{}/state/'.format(address),
                show_response_content=False)


if __name__ == '__main__':
    InstallAgent.autorun()
