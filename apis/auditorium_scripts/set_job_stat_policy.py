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


"""Call the openbach-function set_job_stat_policy"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from functools import partial

from auditorium_scripts.frontend import FrontendBase


class SetJobStatisticsPolicy(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Update Statistic Policy of a Job')
        self.parser.add_argument('agent', help='IP address of the agent')
        self.parser.add_argument('name', help='name of the job to update')
        self.parser.add_argument(
                '-n', '--stat-name',
                help='set the policy only for this specify statistic')
        self.parser.add_argument(
                '-s', '--storage', action='store_true',
                help='allow storage of statistics in the collector')
        self.parser.add_argument(
                '-b', '--broadcast', action='store_true',
                help='allow broadcast of statistics from the collector')
        self.parser.add_argument(
                '-r', '--delete', '--remove', action='store_true',
                help='revert to the default policy')
        self.parser.add_argument(
                '-d', '--date', metavar=('DATE', 'TIME'),
                nargs=2, help='date of the execution')

    def execute(self, show_response_content=True):
        agent = self.args.agent
        job = self.args.name
        statistic = self.args.stat_name
        storage = self.args.storage
        broadcast = self.args.broadcast
        if self.args.delete:
            storage = None
            broadcast = None
        date = self.date_to_timestamp()

        action = self.request
        if storage is not None:
            action = partial(action, storage=storage)
        if broadcast is not None:
            action = partial(action, broadcast=broadcast)
        if date is not None:
            action = partial(action, date=date)

        return action(
                'POST', 'job/{}'.format(job), action='stat_policy',
                stat_name=statistic, addresses=[agent],
                show_response_content=show_response_content)


if __name__ == '__main__':
    SetJobStatisticsPolicy.autorun()
