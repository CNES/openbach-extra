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
__version__ = 'v0.3'


import unittest

from data_access.influxdb_tools import (Operator,
        ConditionAnd, ConditionOr, ConditionField, ConditionTag, ConditionTimestamp,
        escape_names, escape_field, tags_to_condition,
        select_query, measurement_query, delete_query, tag_query,
        parse_influx, parse_statistics, parse_orphans, line_protocol)


class TestDataAccessInfluxDB(unittest.TestCase):
    def test_simple_condition(self):
        field = ConditionField('field_name', Operator.Equal, 42)
        tag = ConditionTag('tag_name', Operator.NotEqual, 0)
        timestamp = ConditionTimestamp(Operator.GreaterThan, 123456789)
        timestamp_from_now = ConditionTimestamp(Operator.Different, 12, 'h', True)

        self.assertEqual(str(field), '"field_name" = 42')
        self.assertEqual(str(tag), '"tag_name" <> \'0\'')
        self.assertEqual(str(timestamp), '"time" > 123456789ms')
        self.assertEqual(str(timestamp_from_now), '"time" != now() - 12h')

    def test_compound_conditions(self):
        condition = ConditionAnd(
            ConditionOr(
                ConditionField('field_name', Operator.GreaterThan, 'a_string'),
                ConditionTag('tag_name', Operator.Different, 'a_string_too'),
            ),
            ConditionTimestamp(Operator.LessThan, 5, 'm', True),
        )
        self.assertEqual(
                str(condition),
                '(("field_name" > \'a_string\') OR ("tag_name" != \'a_string_too\'))'
                ' AND ("time" < now() - 5m)')

    def test_measurement_name_escaping(self):
        for name in ['', 'a', 'a_a', 'a_a_a', '@test']:
            self.assertEqual(escape_names(name, True), name)
        self.assertEqual(escape_names('a a', True), r'a\ a')
        self.assertEqual(escape_names('a,a', True), r'a\,a')
        self.assertEqual(escape_names('a=a', True), r'a=a')

    def test_tags_name_escaping(self):
        for name in ['', 'a', 'a_a', 'a_a_a', '@test']:
            self.assertEqual(escape_names(name, False), name)
        self.assertEqual(escape_names('a a', False), r'a\ a')
        self.assertEqual(escape_names('a,a', False), r'a\,a')
        self.assertEqual(escape_names('a=a', False), r'a\=a')

    def test_fields_escaping(self):
        test_data = (
            ('a', 'a', r'a="a"'),
            ('a_a', 'a', r'a_a="a"'),
            ('a_a', 'a_a', r'a_a="a_a"'),
            ('a', 'a_a', r'a="a_a"'),
            ('a a', 'a', r'a\ a="a"'),
            ('a a', 'a a', r'a\ a="a a"'),
            ('a', 'a a', r'a="a a"'),
            ('a=a', 'a', r'a\=a="a"'),
            ('a=a', 'a=a', r'a\=a="a=a"'),
            ('a', 'a=a', r'a="a=a"'),
            ('a,a', 'a', r'a\,a="a"'),
            ('a,a', 'a,a', r'a\,a="a,a"'),
            ('a', 'a,a', r'a="a,a"'),
            ('a', 0, r'a=0'),
            ('a_a', 0, r'a_a=0'),
            ('a a', 0, r'a\ a=0'),
            ('a=a', 0, r'a\=a=0'),
            ('a,a', 0, r'a\,a=0'),
            ('a', 42, r'a=42'),
            ('a_a', 42, r'a_a=42'),
            ('a a', 42, r'a\ a=42'),
            ('a=a', 42, r'a\=a=42'),
            ('a,a', 42, r'a\,a=42'),
        )
        for field_name, field_value, expected in test_data:
            self.assertEqual(escape_field(field_name, field_value), expected)

    def test_tags_to_condition(self):
        condition_with_nones = tags_to_condition(1, 'toto', None, None)
        self.assertEqual(
                str(condition_with_nones),
                '("@agent_name" = \'toto\') AND '
                '("@scenario_instance_id" = \'1\')')
        condition_all = tags_to_condition(2, 'lulu', 3, 'Test', condition_with_nones)
        self.assertEqual(
                str(condition_all),
                '(("@agent_name" = \'toto\') AND ("@scenario_instance_id" = \'1\'))'
                ' AND ("@agent_name" = \'lulu\') AND ("@scenario_instance_id" = \'2\')'
                ' AND ("@job_instance_id" = \'3\') AND ("@suffix" = \'Test\')')

    def test_queries(self):
        simple_condition = ConditionField('field_name', Operator.Equal, 42)
        select_all = select_query('job_name', [], simple_condition)
        select_few = select_query('job_name', ['a', 'b', 'c'])
        measurement = measurement_query('job', simple_condition)
        with self.assertRaises(AssertionError):
            delete_query(condition=simple_condition)
        delete_all = delete_query(scenario=1, suffix='suffix')
        # TODO: delete_few with a timestamp range as condition
        tags = tag_query('tag_name', 'job_name', simple_condition)

        self.assertEqual(select_all, 'SELECT * FROM "job_name" WHERE "field_name" = 42')
        self.assertEqual(select_few, 'SELECT "a","b","c" FROM "job_name"')
        self.assertEqual(measurement, 'SHOW MEASUREMENTS WITH MEASUREMENT = "job" WHERE "field_name" = 42')
        self.assertEqual(delete_all, 'DROP SERIES FROM /.*/ WHERE ("@scenario_instance_id" = \'1\')'
                                     ' AND ("@suffix" = \'suffix\')')
        self.assertEqual(tags, 'SHOW TAG VALUES FROM "job_name" WITH '
                               'KEY = "tag_name" WHERE "field_name" = 42')

    def test_simple_parse(self):
        data = {'results': [{'series': [{
            'name': 'Debug',
            'columns': [
                'time',
                '@agent_name',
                '@job_instance_id',
                '@owner_scenario_instance_id',
                '@scenario_instance_id',
                'field'],
            'values': [
                [1495094155683, 'Controller', '12', '1000', '100', 1],
                [1495094163291, 'Controller', '12', '1000', '100', 2],
                [1495094165203, 'Controller', '12', '1000', '100', 3],
                [1495094166675, 'Controller', '12', '1000', '100', 4],
                [1495094168131, 'Controller', '12', '1000', '100', 5],
                [1495094169659, 'Controller', '12', '1000', '100', 6]]}]}]}

        expected = [
                ('Debug', {
                    'time': 1495094155683,
                    '@agent_name': 'Controller',
                    '@job_instance_id': '12',
                    '@owner_scenario_instance_id': '1000',
                    '@scenario_instance_id': '100',
                    'field': 1,
                },),
                ('Debug', {
                    'time': 1495094163291,
                    '@agent_name': 'Controller',
                    '@job_instance_id': '12',
                    '@owner_scenario_instance_id': '1000',
                    '@scenario_instance_id': '100',
                    'field': 2,
                },),
                ('Debug', {
                    'time': 1495094165203,
                    '@agent_name': 'Controller',
                    '@job_instance_id': '12',
                    '@owner_scenario_instance_id': '1000',
                    '@scenario_instance_id': '100',
                    'field': 3,
                },),
                ('Debug', {
                    'time': 1495094166675,
                    '@agent_name': 'Controller',
                    '@job_instance_id': '12',
                    '@owner_scenario_instance_id': '1000',
                    '@scenario_instance_id': '100',
                    'field': 4,
                },),
                ('Debug', {
                    'time': 1495094168131,
                    '@agent_name': 'Controller',
                    '@job_instance_id': '12',
                    '@owner_scenario_instance_id': '1000',
                    '@scenario_instance_id': '100',
                    'field': 5,
                },),
                ('Debug', {
                    'time': 1495094169659,
                    '@agent_name': 'Controller',
                    '@job_instance_id': '12',
                    '@owner_scenario_instance_id': '1000',
                    '@scenario_instance_id': '100',
                    'field': 6,
                },),
        ]
        self.assertEqual(list(parse_influx(data)), expected)

    def test_statistics_parse(self):
        data = {'results': [{'series': [{
            'name': 'Debug',
            'columns': [
                'time',
                '@agent_name',
                '@job_instance_id',
                '@owner_scenario_instance_id',
                '@scenario_instance_id',
                'field'],
            'values': [
                [1495094155683, 'Controller', '12', '1000', '100', 1],
                [1495094163291, 'Controller', '12', '1000', '100', 2],
                [1495094165203, 'Controller', '12', '1000', '100', 3],
                [1495094166675, 'Controller', '12', '1000', '100', 4],
                [1495094168131, 'Controller', '12', '1000', '100', 5],
                [1495094169659, 'Controller', '12', '1000', '100', 6]]}]}]}

        scenario, owner = parse_statistics(data)
        self.assertEqual(scenario.instance_id, '100')
        self.assertEqual(scenario.owner_instance_id, '1000')
        self.assertEqual(owner.instance_id, '1000')
        self.assertEqual(list(owner.jobs), [])
        job, = scenario.jobs
        self.assertEqual(job.name, 'Debug')
        self.assertEqual(job.agent, 'Controller')
        self.assertEqual(job.instance_id, '12')
        statistics = job.statistics_data[(None,)]
        expected = [
                {'time': 1495094155683, 'field': 1},
                {'time': 1495094163291, 'field': 2},
                {'time': 1495094165203, 'field': 3},
                {'time': 1495094166675, 'field': 4},
                {'time': 1495094168131, 'field': 5},
                {'time': 1495094169659, 'field': 6},
        ]
        self.assertEqual(statistics.json, expected)

    # TODO test_orphans_parse, test_line_protocol / test_f


if __name__ == '__main__':
    unittest.main()
