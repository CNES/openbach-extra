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


"""Call the openbach-function start_scenario_instance"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from functools import partial

from auditorium_scripts.frontend import FrontendBase


class StartScenarioInstance(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Start a Scenario')
        self.parser.add_argument(
                'scenario_name',
                help='name of the scenario to start')
        self.parser.add_argument(
                'project_name',
                help='name of the project the scenario is associated with')
        self.parser.add_argument(
                '-a', '--argument', nargs=2, default=[],
                action='append', metavar=('NAME', 'VALUE'),
                help='value of an argument of the scenario')
        self.parser.add_argument(
                '-d', '--date', nargs=2, metavar=('DATE', 'TIME'),
                help='date of the execution')

    def execute(self, show_response_content=True):
        scenario = self.args.scenario_name
        project = self.args.project_name
        arguments = dict(self.args.argument)
        date = self.date_to_timestamp()

        action = partial(self.request, arguments=arguments)
        if date is not None:
            action = partial(action, date=date)

        route = 'project/{}/scenario/{}/scenario_instance/'.format(project, scenario)
        return action('POST', route, show_response_content=show_response_content)


if __name__ == '__main__':
    StartScenarioInstance.autorun()
