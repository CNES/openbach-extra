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


"""Call the openbach-function manage_databases"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Léa Thibout <lea.thibout@viveris.fr>
'''


from auditorium_scripts.frontend import FrontendBase, pretty_print
from functools import partial

class ManageDatabases(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Manage databases')
        self.parser.add_argument('--address', type=str, required=True, help='Collector address on which is the database')
        self.parser.add_argument('--influxdb', action='store_true', help='Present if we want to empty influxdb database.')
        self.parser.add_argument('--elasticsearch', action='store_true', help='Present if we want to empty elasticsearch database')
        self.parser.add_argument('command', choices=['get', 'delete'])

    def execute(self, show_response_content=True):
        command = self.args.command
        influxdb = self.args.influxdb
        elasticsearch = self.args.elasticsearch
        address = self.args.address

        params = {'address': address}
        if influxdb:
            params['influxdb'] = True
        if elasticsearch:
            params['elasticsearch'] = True

        if command == 'get':
            response = self.request('GET', 'databases', 
                    show_response_content=show_response_content, **params)
        elif command == 'delete':
            response = self.request('DELETE', 'databases', 
                    show_response_content=show_response_content, **params)
        return response

if __name__ == '__main__':
    ManageDatabases.autorun()
