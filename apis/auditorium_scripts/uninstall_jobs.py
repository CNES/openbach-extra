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


"""Call the openbach-function uninstall_jobs"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import inspect
import itertools
import threading

from auditorium_scripts.frontend import FrontendBase
from auditorium_scripts.state_job import StateJob


class WaitForUninstall(threading.Thread):
    def run(self):
        try:
            result = self._run()
        except Exception as e:
            self._exception = e
        else:
            self._exception = None
            self._result = result


    def _run(self):
        signature = inspect.signature(lambda state_job, show_response_content=None: None)
        arguments = signature.bind(*self._args, **self._kwargs)
        arguments.apply_defaults()

        state_job = arguments.arguments['state_job']
        show = arguments.arguments['show_response_content']
        if show is None:
            return state_job.wait_for_success('uninstall')
        else:
            return state_job.wait_for_success('uninstall', show_response_content=show)

    def join(self, timeout=None):
        super().join(timeout)
        if self._exception is not None:
            raise self._exception
        return self._result


class UninstallJobs(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Uninstall Jobs')
        self.parser.add_argument(
                '-j', '--job-name', '--job', metavar='NAME', action='append',
                nargs='+', required=True, help='Name of the Jobs to install '
                'on the next agent. May be specified several times to '
                'install different sets of jobs on different agents.')
        self.parser.add_argument(
                '-a', '--agent-address', '--agent', metavar='ADDRESS',
                action='append', nargs='+', required=True, help='IP address '
                'of the agent where the next set of jobs should be installed. '
                'May be specified several times to install different sets of '
                'jobs on different agents.')
        self.parser.add_argument(
                '-l', '--launch', '--launch-only', action='store_true',
                help='do not wait until installation of the jobs completes '
                'on each agent; return as soon as orders have been sent.')

    def parse(self, args=None):
        super().parse(args)
        jobs = self.args.job_name
        agents = self.args.agent_address

        if len(jobs) != len(agents):
            self.parser.error('-j and -a arguments should appear by pairs')

    def execute(self, show_response_content=True):
        jobs_names = self.args.job_name
        agents_ips = self.args.agent_address
        launch_only = self.args.launch
        check_status = len(jobs_names) == 1

        responses = [
                self.request(
                    'POST', 'job', action='uninstall',
                    names=jobs, addresses=agents,
                    show_response_content=launch_only and show_response_content,
                    check_status=check_status)
                for agents, jobs in zip(agents_ips, jobs_names)
        ]

        if launch_only:
            if show_response_content and not check_status:
                for response in responses:
                    response.raise_for_status()
        else:
            threads = list(self._start_monitoring(show_response_content))
            responses = [thread.join() for thread in threads]

        return responses

    def _start_monitoring(self, show_response_content=True):
        for agents, jobs in zip(self.args.agent_address, self.args.job_name):
            for agent, job in itertools.product(agents, jobs):
                state_job = self.share_state(StateJob)
                state_job.args.job_name = job
                state_job.args.agent_address = agent
                thread = WaitForUninstall(args=(state_job, show_response_content))
                thread.start()
                yield thread


if __name__ == '__main__':
    UninstallJobs.autorun()
