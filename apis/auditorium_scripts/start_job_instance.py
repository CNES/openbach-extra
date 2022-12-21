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


"""Call the openbach-function start_job_instance"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import shlex
import argparse
from functools import partial

from auditorium_scripts.frontend import FrontendBase, DEFAULT_DATE_FORMAT


class Argument(argparse.Action):
    PARENTS = 0

    def __call__(self, parser, args, values, option_string=None):
        items = getattr(args, self.dest)
        if items is None:
            items = {}
            setattr(args, self.dest, items)

        self._parse_command_line(items, values)

    def _parse_command_line(self, items, values):
        for _ in range(self.PARENTS):
            try:
                subcommand, *arguments = values
            except ValueError as e:
                raise argparse.ArgumentError(self, e)
            else:
                items = items.setdefault(subcommand, {})
                values = arguments

        if values:
            try:
                name, *values = values
            except ValueError as e:
                raise argparse.ArgumentError(self, e)

            items[name] = values or [True]


class SubCommand(Argument):
    PARENTS = 1


class SubSubCommand(Argument):
    PARENTS = 2


class SubSubSubCommand(Argument):
    PARENTS = 3


class SubSubSubSubCommand(Argument):
    PARENTS = 4


class SubSubSubSubSubCommand(Argument):
    PARENTS = 5


class StartJobInstance(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Start Job Instance')
        self.parser.add_argument('agent_address', help='IP address or domain of the agent')
        self.parser.add_argument('job_name', help='name of the job to start')
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
        agent = self.args.agent_address
        job_name = self.args.job_name
        arguments = self.args.argument
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
