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


"""Call the openbach-function reboot"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Léa Thibout <lea.thibout@viveris.fr>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from auditorium_scripts.frontend import FrontendBase, pretty_print
from functools import partial


class Reboot(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Reboot')
        self.parser.add_argument('agent_address', help='IP address of the agent')
        self.parser.add_argument(
                '--kernel',
                help='kernel name on which we will reboot; '
                'leave empty to reboot on the default kernel')

    def execute(self, show_response_content=True):
        agent = self.args.agent_address
        kernel = self.args.kernel

        action = self.request 
        if kernel is not None:
            action = partial(action, kernel=kernel)

        return action('POST', 'reboot/', agent_ip=agent,
                show_response_content=show_response_content)


if __name__ == '__main__':
    Reboot.autorun()
