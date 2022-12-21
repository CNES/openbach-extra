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


"""Call the openbach-function restart_job_instance"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import shlex
from functools import partial

from auditorium_scripts.frontend import FrontendBase, DEFAULT_DATE_FORMAT
from auditorium_scripts.start_job_instance import (
        Argument, SubCommand, SubSubCommand, SubSubSubCommand,
        SubSubSubSubCommand, SubSubSubSubSubCommand,
)


class RestartJobInstance(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Restart Job Instance')
        self.parser.add_argument(
                'job_instance_id', type=int,
                help='id of the job instance to restart')
        self.parser.add_argument(
                '-a', '--argument', nargs='+', action=Argument, metavar=('NAME', 'VALUE'),
                help='description of an argument with its name and associated value(s)')
        self.parser.add_argument(
                '-s', '--sub-command', dest='argument', nargs='+', action=SubCommand,
                metavar=('SUBCOMMAND', 'ARGUMENT_DESCRIPTION'),
                help='description of sub-command with its name and associated argument description (name and value(s), see "-a")')
        self.parser.add_argument(
                '--sub-sub-command', dest='argument', nargs='+', action=SubSubCommand,
                metavar=('SUBSUBCOMMAND', 'SUBCOMMAND_DESCRIPTION'),
                help='description of sub-sub-command with its name and associated sub-command description (name and argument, see "-s")')
        self.parser.add_argument(
                '--sub-sub-sub-command', dest='argument', nargs='+', action=SubSubSubCommand,
                metavar=('SUBSUBSUBCOMMAND', 'SUBSUBCOMMAND_DESCRIPTION'),
                help='description of sub-sub-sub-command with its name and associated sub-sub-command description')
        self.parser.add_argument(
                '--sub-sub-sub-sub-command', dest='argument', nargs='+', action=SubSubSubSubCommand,
                metavar=('SUBSUBSUBSUBCOMMAND', 'SUBSUBSUBCOMMAND_DESCRIPTION'),
                help='description of sub-sub-sub-sub-command with its name and associated sub-sub-sub-command description')
        self.parser.add_argument(
                '--sub-sub-sub-sub-sub-command', dest='argument', nargs='+', action=SubSubSubSubSubCommand,
                metavar=('SUBSUBSUBSUBSUBCOMMAND', 'SUBSUBSUBSUBCOMMAND_DESCRIPTION'),
                help='description of sub-sub-sub-sub-sub-command with its name and associated sub-sub-sub-sub-command description')
        group = self.parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
                '-d', '--date', metavar=('DATE', 'TIME'), nargs=2,
                help='date at which the job execution should start ({})'
                        .format(DEFAULT_DATE_FORMAT.replace('%', '%%')))
        group.add_argument(
                '-i', '--interval', type=int,
                help='schedule repetitions of the job execution every '
                     '"interval" seconds until the job is stopped')

    def execute(self, show_response_content=True):
        instance_id = self.args.job_instance_id
        arguments = self.args.argument
        date = self.date_to_timestamp()
        interval = self.args.interval

        action = self.request
        if interval is not None:
            action = partial(action, interval=interval)
        if date is not None:
            action = partial(action, date=date)

        return action(
                'POST', 'job_instance/{}/'.format(instance_id),
                action='restart', instance_args=arguments,
                show_response_content=show_response_content)


if __name__ == '__main__':
    RestartJobInstance.autorun()
