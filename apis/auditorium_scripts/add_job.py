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


"""Call the openbach-function add_job"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import os
import tarfile
import tempfile

from auditorium_scripts.frontend import FrontendBase


class AddJob(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Add Job on the Controller')
        self.parser.add_argument('job_name', help='name of the job')
        job_options = self.parser.add_mutually_exclusive_group(required=True)
        job_options.add_argument(
                '-p', '--path', help='path to the folder (on the controller) '
                'containing the install and uninstall playbooks of the job')
        job_options.add_argument(
                '-f', '--files', help='path to the folder (on the local machine) '
                'containing the install and uninstall playbooks of the job')
        job_options.add_argument(
                '-t', '--tarball', help='path to a .tar.gz file containing '
                'the install and uninstall playbooks of the job')

    def execute(self, show_response_content=True):
        job_name = self.args.job_name
        path = self.args.path
        files = self.args.files
        tarball = self.args.tarball

        if path is not None:
            return self.request(
                    'POST', 'job', name=job_name, path=path,
                    show_response_content=show_response_content)

        if files is not None:
            os.chdir(os.path.expanduser(files))
            with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tar_path:
                tarball = tar_path.name
            with tarfile.open(tarball, mode='w:gz') as tar:
                for filename in os.listdir('.'):
                    tar.add(filename)

        if tarball is not None:
            with open(os.path.expanduser(tarball), 'rb') as tarball_file:
                return self.request(
                        'POST', 'job', name=job_name,
                        files={'file': tarball_file},
                        show_response_content=show_response_content)


if __name__ == '__main__':
    AddJob.autorun()
