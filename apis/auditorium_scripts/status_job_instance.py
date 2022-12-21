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


"""Call the openbach-function status_job_instance"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from functools import partial

from auditorium_scripts.frontend import FrontendBase


class StatusJobInstance(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Status Job Instance')
        self.parser.add_argument('job_instance_id', help='id of the instance')
        self.parser.add_argument(
                '-u', '--update', action='store_true',
                help='contact the agent to retrieve the last status')

    def execute(self, show_response_content=True):
        instance_id = self.args.job_instance_id
        update = self.args.update

        action = self.request
        if update:
            action = partial(action, update='')

        return action(
                'GET', 'job_instance/{}/'.format(instance_id),
                show_response_content=show_response_content)


if __name__ == '__main__':
    StatusJobInstance.autorun()
