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


"""Call the openbach-function start_job_instance"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import shlex
from functools import partial

from frontend import FrontendBase


def parse(value):
    name, *values = shlex.split(value, posix=True)
    return name, values


class StartJobInstance(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Start Job Instance')
        self.parser.add_argument('agent', help='IP address of the agent')
        self.parser.add_argument('name', help='name of the job to start')
        self.parser.add_argument(
                '-a', '--argument', type=parse, nargs='+', default={},
                metavar='NAME[ VALUE[ VALUE...]]',
                help='')
        group = self.parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
                '-d', '--date', metavar=('DATE', 'TIME'),
                nargs=2, help='date of the execution')
        group.add_argument(
                '-i', '--interval', type=int,
                help='interval of the execution')

    def execute(self, show_response_content=True):
        agent = self.args.agent
        job_name = self.args.name
        arguments = dict(self.args.argument)
        date = self.date_to_timestamp()
        interval = self.args.interval

        action = self.request
        if interval is not None:
            action = partial(action, interval=interval)
        if date is not None:
            action = partial(action, date=date)

        return action(
                'POST', 'job_instance', action='start',
                agent_ip=agent, job_name=job_name, instance_args=arguments,
                show_response_content=show_response_content)


if __name__ == '__main__':
    StartJobInstance.autorun()
