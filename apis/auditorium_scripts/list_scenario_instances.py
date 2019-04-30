#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2019 CNES
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


"""Call the openbach-function list_scenario_instance"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from auditorium_scripts.frontend import FrontendBase


class ListScenarioInstances(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — List Instances of a Scenario')
        self.parser.add_argument(
                '-s', '--scenario',
                help='name of the scenario whose instances should be listed')
        self.parser.add_argument(
                '-p', '--project',
                help='name of the project the scenario is associated with')

    def execute(self, show_response_content=True):
        scenario = self.args.scenario
        project = self.args.project

        route = 'scenario_instance/'
        if project is not None:
            prepend = 'project/{}/'.format(project)
            if scenario is not None:
                prepend = '{}scenario/{}/'.format(prepend, scenario)
            route = prepend + route

        return self.request('GET', route, show_response_content=show_response_content)


if __name__ == '__main__':
    ListScenarioInstances.autorun()
