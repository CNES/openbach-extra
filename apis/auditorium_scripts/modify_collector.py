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


"""Call the openbach-function modify_collector"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from functools import partial

from auditorium_scripts.frontend import FrontendBase


class ModifyCollector(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Modify Collector')
        self.parser.add_argument(
                'collector_address',
                help='new IP address of the collector')
        self.parser.add_argument(
                '-l', '--logs-port', type=int,
                help='new port for the logs')
        self.parser.add_argument(
                '-s', '--stats-port', type=int,
                help='new port for the stats')

    def execute(self, show_response_content=True):
        collector = self.args.collector_address
        logs_port = self.args.logs_port
        stats_port = self.args.stats_port

        action = self.request
        if logs_port is not None:
            action = partial(action, logs_port=logs_port)
        if stats_port is not None:
            action = partial(action, stats_port=stats_port)
        return action(
                'PUT', 'collector/{}'.format(collector),
                show_response_content=show_response_content)


if __name__ == '__main__':
    ModifyCollector.autorun()
