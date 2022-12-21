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


"""Call the openbach-function uninstall_jobs for all jobs installed on any agent"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from auditorium_scripts.frontend import FrontendBase
from auditorium_scripts.list_agents import ListAgents
from auditorium_scripts.list_installed_jobs import ListInstalledJobs
from auditorium_scripts.uninstall_jobs import UninstallJobs


class UninstallAllJobs(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Uninstall all Jobs on all the Agents')
        self.parser.add_argument(
                '-l', '--launch', '--launch-only', action='store_true',
                help='do not wait until uninstallation of the jobs completes '
                'on each agent; return as soon as orders have been sent.')
        self.parser.set_defaults(update=False, services=False)

    def execute(self, show_response_content=True):
        agents = self.share_state(ListAgents)
        response = agents.execute(False)
        response.raise_for_status()

        job_names = []
        addresses = []
        for agent in response.json():
            address = agent['address']

            jobs = self.share_state(ListInstalledJobs)
            jobs.args.agent_address = address
            response = jobs.execute(False)
            response.raise_for_status()

            job_names.append([job['name'] for job in response.json()['installed_jobs']])
            addresses.append([address])

        uninstaller = self.share_state(UninstallJobs)
        uninstaller.args.job_name = job_names
        uninstaller.args.agent_address = addresses
        return uninstaller.execute(show_response_content)

if __name__ == '__main__':
	UninstallAllJobs.autorun()
