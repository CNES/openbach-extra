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


"""Call the openbach-function add_entity"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from auditorium_scripts.frontend import FrontendBase


class AddEntity(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH – Add a new Entity into a Project')
        self.parser.add_argument('entity_name', help='name of the entity')
        self.parser.add_argument('project_name', help='name of the project')
        self.parser.add_argument(
                '-d', '--description',
                help='explanation of the entity role')
        self.parser.add_argument(
                '-a', '--agent-address', '--agent',
                help='address of an agent to associate with the entity')

    def execute(self, show_response_content=True):
        project_name = self.args.project_name
        description = self.args.description
        agent = self.args.agent_address

        entity = {'name': self.args.entity_name}
        if description:
            entity['description'] = description
        if agent:
            entity['agent'] = {'address': agent}

        return self.request(
                'POST', 'project/{}/entity/'.format(project_name),
                **entity, show_response_content=show_response_content)


if __name__ == '__main__':
    AddEntity.autorun()
