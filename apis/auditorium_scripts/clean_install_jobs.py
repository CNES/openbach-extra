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


"""Call the openbach-functions uninstall_jobs and install_jobs"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from auditorium_scripts.frontend import FrontendBase
from auditorium_scripts.install_jobs import InstallJobs
from auditorium_scripts.uninstall_jobs import UninstallJobs
from auditorium_scripts.delete_job import DeleteJob
from auditorium_scripts.add_job import AddJob


class CleanInstallJob(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Install Job on agents after Uninstalling it first'
		'This script requires that the job is already installed on Agents.')
        self.parser.add_argument(
                'job_name', metavar='NAME',
                help='Name of the Job to install on the specified agents.')
        self.parser.add_argument(
                '-a', '--agent-address', '--agent', metavar='ADDRESS',
                action='append', required=True, default=[],
                help='IP address of the agents where the job should be installed.')
        self.parser.set_defaults(launch=False, clean_controller=False)

        subparsers = self.parser.add_subparsers(title='extra action')
        parser = subparsers.add_parser('clean_controller')
        job_options = parser.add_mutually_exclusive_group(required=True)
        job_options.add_argument(
                '-p', '--path', help='path to the folder (on the controller) '
                'containing the install and uninstall playbooks of the job')
        job_options.add_argument(
                '-f', '--files', help='path to the folder (on the local machine) '
                'containing the install and uninstall playbooks of the job')
        job_options.add_argument(
                '-t', '--tarball', help='path to a .tar.gz file containing '
                'the install and uninstall playbooks of the job')
        parser.set_defaults(clean_controller=True)

    def execute(self, show_response_content=True):
        uninstaller = self.share_state(UninstallJobs)
        uninstaller.args.job_name = [[self.args.job_name]]
        uninstaller.args.agent_address = [self.args.agent_address]
        uninstaller.execute(False)

        if self.args.clean_controller:
            deleter = self.share_state(DeleteJob)
            deleter.execute(False)
            adder = self.share_state(AddJob)
            adder.execute(show_response_content)

        installer = self.share_state(InstallJobs)
        installer.args.job_name = [[self.args.job_name]]
        installer.args.agent_address = [self.args.agent_address]
        return installer.execute(show_response_content)


if __name__ == '__main__':
    CleanInstallJob.autorun()
