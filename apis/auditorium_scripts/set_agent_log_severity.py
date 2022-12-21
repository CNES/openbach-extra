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


"""Call the openbach-function set_agent_log_severity"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from functools import partial

from auditorium_scripts.frontend import FrontendBase


class SetAgentLogSeverity(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Update Log Severity of an Agent')
        self.parser.add_argument('agent_address', help='IP address of the agent')
        self.parser.add_argument(
                'severity', choices=range(1, 5), type=int,
                help='severity up to which logs are sent to the collector')
        self.parser.add_argument(
                '-l', '--local-severity', choices=range(1, 5), type=int,
                help='severity up to which logs are saved on the agent')

    def execute(self, show_response_content=True):
        agent = self.args.agent_address
        severity = self.args.severity
        local_severity = self.args.local_severity

        action = self.request
        if local_severity is not None:
            action = partial(action, local_severity=local_severity)

        return action(
                'POST', 'agent/{}/'.format(agent),
                action='log_severity', severity=severity,
                show_response_content=show_response_content)


if __name__ == '__main__':
    SetAgentLogSeverity.autorun()
