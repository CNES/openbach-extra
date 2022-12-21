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


"""Call the openbach-function set_job_stat_policy"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from functools import partial

from auditorium_scripts.frontend import FrontendBase

class SetJobStatsPolicy(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Update Statistic Policy of a Job')
        self.parser.add_argument('agent_address', help='IP address of the agent')
        self.parser.add_argument('job_name', help='name of the job to update')
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
                '-l', '--local', action='store_true',
                help='allow storage of statistics locally in the agent')
        self.parser.add_argument(
                '-r', '--delete', '--remove', action='store_true',
                help='revert to the default policy')
        self.parser.add_argument(
                '-p', '--path',
                help='path to the rstats default conf file on the controller. Needed with r/delete/remove parameter')
        self.parser.add_argument(
                '-f', '--filename',
                help='name of or path to the configuration file on the '
                'agent; defaults to /opt/openbach/agent/jobs/<job_name>/'
                '<job_name>_rstats.conf if not specified')

    def execute(self, show_response_content=True):
        agent = self.args.agent_address
        job = self.args.job_name
        statistic = self.args.stat_name
        storage = self.args.storage
        broadcast = self.args.broadcast
        local = self.args.local
        path = self.args.path
        if self.args.delete:
            if not path and not statistic:
                self.parser.error('-r/--delete/--remove requires path argument')
            elif path and not statistic:
                print('WARNING: Don\'t forget to also launch the -r with the stats name to restore the default policy for the previously modified stats if any.')
            storage = None
            broadcast = None
            local = None
        filename = self.args.filename

        action = self.request
        if storage is not None:
            action = partial(action, storage=storage)
        if broadcast is not None:
            action = partial(action, broadcast=broadcast)
        if local is not None:
            action = partial(action, local=local)
        if filename is not None:
            action = partial(action, config_file=filename)
        if self.args.delete:
            action = partial(action, path=path)

        return action(
                'POST', 'job/{}'.format(job), action='stat_policy',
                stat_name=statistic, addresses=[agent],
                show_response_content=show_response_content)


if __name__ == '__main__':
    SetJobStatsPolicy.autorun()
