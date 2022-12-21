#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2023 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

__author__ = 'Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>'
__version__ = 'v0.1'


import sys
import argparse
import unittest

import data_access


COLLECTOR_IP = None


class TestDataImportExport(unittest.TestCase):
    def setUp(self):
        if COLLECTOR_IP is None:
            self.skipTest('No collector found')
        self.collector = data_access.CollectorConnection(COLLECTOR_IP)

    def _test_import(self, filename):
        scenario = data_access.read_scenario(filename)
        self.collector.import_scenario(scenario)
        retrieved, = self.collector.scenarios(
                scenario_instance_id=scenario.instance_id)
        self.assertEqual(retrieved, scenario)

    def test_import_netcat(self):
        self._test_import('netcat.json')

    def test_import_ping(self):
        self._test_import('ping.json')

    def test_import_mptcp(self):
        self._test_import('mptcp_socat.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--collector', metavar='IP')
    args, remaining = parser.parse_known_args()
    COLLECTOR_IP = args.collector
    if '-h' in remaining or '--help' in remaining:
        # Handle extra help ourselves
        print('--------------- Extra test arguments ---------------\n')
        parser.print_help()
        print('\n--------------- Regular unittest arguments ---------------\n')
    remaining.insert(0, sys.argv[0])
    unittest.main(argv=remaining)
