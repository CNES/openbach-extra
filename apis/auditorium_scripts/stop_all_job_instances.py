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


"""Call the openbach-functions list_job_instances then stop_job_instances"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from auditorium_scripts.frontend import FrontendBase, pretty_print
from auditorium_scripts.list_job_instances import ListJobInstances
from auditorium_scripts.stop_job_instance import StopJobInstance


class StopAllJobInstances(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH − List and Stop Job Instances from agents')
        self.parser.add_argument(
                'agent_address', nargs='+',
                help='IP addresses of the agents')
        self.parser.add_argument(
                '-j', '--job-name', '--job', action='append', default=[],
                help='Name of the job to stop. Can be used several times. Leave empty to stop all jobs.')
        self.parser.add_argument(
                '-d', '--date', metavar=('DATE', 'TIME'),
                nargs=2, help='date of the execution')

    def execute(self, show_response_content=True):
        jobs_lister = self.share_state(ListJobInstances)
        jobs_lister.args.update = True
        jobs_list = jobs_lister.execute(False)
        jobs_list.raise_for_status()

        jobs_to_stop = set(self.args.job_name)
        instances = [
                instance['id']
                for agent in jobs_list.json()['instances']
                for job in agent['installed_jobs']
                for instance in job['instances']
                if not jobs_to_stop or instance['name'] in jobs_to_stop
        ]
        jobs_stopper = self.share_state(StopJobInstance)
        jobs_stopper.args.job_instance_id = instances
        return jobs_stopper.execute(show_response_content)


if __name__ == '__main__':
    StopAllJobInstances.autorun()
