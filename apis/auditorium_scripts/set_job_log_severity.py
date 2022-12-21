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


"""Call the openbach-function set_job_log_severity"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from functools import partial

from auditorium_scripts.frontend import FrontendBase


class SetJobLogSeverity(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Update Log Severity of a Job')
        self.parser.add_argument('agent_address', help='IP address of the agent')
        self.parser.add_argument('job_name', help='name of the job to update')
        self.parser.add_argument(
                'severity', choices=range(1, 5), type=int,
                help='severity up to which logs are sent to the collector')
        self.parser.add_argument(
                '-l', '--local-severity', choices=range(1, 5), type=int,
                help='severity up to which logs are saved on the agent')
        self.parser.add_argument(
                '-d', '--date', metavar=('DATE', 'TIME'),
                nargs=2, help='date of the execution')

    def execute(self, show_response_content=True):
        agent = self.args.agent_address
        job = self.args.job_name
        severity = self.args.severity
        local_severity = self.args.local_severity
        date = self.date_to_timestamp()

        action = self.request
        if local_severity is not None:
            action = partial(action, local_severity=local_severity)
        if date is not None:
            action = partial(action, date=date)

        return action(
                'POST', 'job/{}/'.format(job), action='log_severity',
                addresses=[agent], severity=severity,
                show_response_content=show_response_content)


if __name__ == '__main__':
    SetJobLogSeverity.autorun()
