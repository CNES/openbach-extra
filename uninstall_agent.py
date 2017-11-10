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


"""Call the openbach-function uninstall_agent"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from frontend import FrontendBase


class UninstallAgent(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Uninstall Agent')
        self.parser.add_argument('agent', help='IP address of the agent')

    def execute(self):
        address = self.args.agent
        self.request(
                'DELETE', 'agent/{}/'.format(address),
                show_response_content=False)
        self.wait_for_success('uninstall')

    def query_state(self):
        address = self.args.agent
        self.request(
                'GET', 'agent/{}/state/'.format(address),
                show_response_content=False)


if __name__ == '__main__':
    UninstallAgent.autorun()
