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


"""Call the openbach-function install_jobs"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from frontend import FrontendBase


class InstallJob(FrontendBase):
    def __init__(self):
        super().__init__(self)
        self.parser.add_argument(
                '-j', '--job-name', metavar='NAME', action='append',
                nargs='+', required=True, help='Name of the Jobs to install '
                'on the next agent. May be specified several times to '
                'install different sets of jobs on different agents.')
        self.parser.add_argument(
                '-a', '--agent', metavar='ADDRESS', action='append',
                required=True, help='IP address of the agent where the next '
                'set of jobs should be installed. May be specified several '
                'times to install different sets of jobs on different agents.')

    def parse(self, args=None):
        super().parse(args)
        jobs = self.args.job_name
        agents = self.args.agent

        if len(jobs) != len(agents):
            self.parser.error('-j and -a arguments should appear by pairs')

    def execute(self, show_response_content=True):
        jobs_names = self.args.job_name
        agents_ips = self.args.agent

        return [
                self.request(
                    'POST', 'job', action='install',
                    names=jobs, addresses=agents,
                    show_response_content=show_response_content)
                for agents, jobs in zip(agents_ips, jobs_names)
        ]


if __name__ == '__main__':
    InstallJob.autorun()
