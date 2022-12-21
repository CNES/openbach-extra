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

"""Collection of tools to fetch information from an InfluxDB server.

This module provide:
    * `InfluxDBConnection`: a class to fetch and send data to/from
    an InfluxDB server.
    * generic tools to format data when sending them to InfluxDB.
    * `Condition` classes to help build WHERE clauses in queries.
"""

__author__ = 'Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>'
__credits__ = 'Maintainer: Mathias ETTINGER <mettinger@toulouse.viveris.com>'
__all__ = [
    'InfluxDBConnection',
    'Operator',
    'ConditionAnd',
    'ConditionOr',
    'ConditionTag',
    'ConditionField',
    'ConditionTimestamp',
]


import re
import sys
import enum
import itertools
from collections import defaultdict
from contextlib import suppress

import requests

from .result_data import Scenario, get_or_create_scenario


#########################################
# Conditions: helpers for WHERE clauses #
#########################################

class Condition:
    """Generic Condition"""

    @property
    def is_timestamp(self):
        """Indicates whether or not this condition is only
        about timestamps.

        As time has a special meaning for InfluxDB this
        allow to filter queries.
        """
        return False

    def __str__(self):
        return "{}".format(self)


class BooleanCondition(Condition):
    """Matches as the result of a boolean comparison
    on the match of other conditions.
    """

    def __init__(self, *conditions):
        assert all(isinstance(c, Condition) for c in conditions)
        self.conditions = conditions

    @property
    def is_timestamp(self):
        return all(c.is_timestamp for c in self.conditions)

    def __format__(self, format_spec):
        separator = ' {} '.format(self.KEYWORD)
        return separator.join(map('({})'.format, self.conditions))


class ConditionAnd(BooleanCondition):
    """Matches when other conditions do as well"""
    KEYWORD = 'AND'


class ConditionOr(BooleanCondition):
    """Matches when either one of other conditions do as well"""
    KEYWORD = 'OR'


class Operator(enum.Enum):
    Equal = '='
    NotEqual = '<>'
    Different = '!='
    GreaterThan = '>'
    GreaterOrEqual = '>='
    LessThan = '<'
    LessOrEqual = '<='
    Matches = '=~'
    DoesNotMatch = '!~'


class ComparatorCondition(Condition):
    """Matches as a comparison is made between a tag/field and a value"""

    def __init__(self, name, operator, value):
        assert isinstance(name, str)
        assert isinstance(operator, Operator)
        self.name = name
        self.operator = operator
        self.value = value

    def __format__(self, format_spec):
        return '"{}" {} {}'.format(self.name, self.operator.value, self.escaped_value)


class ConditionTag(ComparatorCondition):
    """Matches as a tag satisfies a comparison"""

    @property
    def escaped_value(self):
        return "'{}'".format(self.value)


class ConditionField(ComparatorCondition):
    """Matches as a field satisfies a comparison"""

    @property
    def escaped_value(self):
        if isinstance(self.value, str):
            return "'{}'".format(self.value)
        return self.value


class ConditionTimestamp(ComparatorCondition):
    """Matches as the timestamp satisfies a comparison"""

    def __init__(self, operator, value, unit='ms', from_now=False):
        super().__init__("time", operator, value)
        assert operator not in (Operator.Matches, Operator.DoesNotMatch)
        pattern = 'now() - {}{}' if from_now else '{}{}'
        self.escaped_value = pattern.format(value, unit)
        

    @property
    def is_timestamp(self):
        return True

    @classmethod
    def from_timestamps(cls, timestamps):
        try:
            timestamp_lower, timestamp_upper = timestamps
        except (TypeError, ValueError):
            return cls(Operator.Equal, timestamps)
        else:
            return ConditionAnd(
                cls(Operator.GreaterOrEqual, timestamp_lower),
                cls(Operator.LessOrEqual, timestamp_upper))


############################################
# Helper functions for formatting purposes #
############################################

LINE_PROTOCOL_CHUNCK_SIZE = 4000
MEASUREMENT_SPECIALS = re.compile(r'[ ,]')
TAGS_AND_FIELDS_SPECIALS = re.compile(r'[ ,=]')
FIELDS_VALUE_SPECIALS = re.compile(r'["]')


def escape_names(name, measurement=False):
    """Escape measurements and fields names as per InfluxDB parsing rules.

    See https://docs.influxdata.com/influxdb/v1.2/
    write_protocols/line_protocol_reference/#special-characters
    for details.
    """
    if measurement:
        return MEASUREMENT_SPECIALS.sub(r'\\\g<0>', name)
    return TAGS_AND_FIELDS_SPECIALS.sub(r'\\\g<0>', name)


def escape_field(name, value):
    """Format field names and values as per InfluxDB parsing rules.

    See https://docs.influxdata.com/influxdb/v1.2/
    write_protocols/line_protocol_reference/ for details.
    """
    if isinstance(value, str):
        value = '"{}"'.format(FIELDS_VALUE_SPECIALS.sub(r'\\\g<0>', value))
    return '{}={}'.format(TAGS_AND_FIELDS_SPECIALS.sub(r'\\\g<0>', name), value)


def tags_to_condition(scenario, agent, job_instance, suffix, extra_condition=None, *, subscenarios=False):
    """Concatenate the given tags values into a single condition"""

    tags = {
        '@agent_name': agent,
        '@job_instance_id': job_instance,
        '@suffix': suffix,
    }
    conditions = [
            ConditionTag(name, Operator.Equal, value)
            for name, value in tags.items()
            if value is not None
    ]

    if scenario is not None:
        scenario_condition = ConditionTag('@scenario_instance_id', Operator.Equal, scenario)
        if subscenarios:
            owner_condition = ConditionTag('@owner_scenario_instance_id', Operator.Equal, scenario)
            scenario_condition = ConditionOr(scenario_condition, owner_condition)
        conditions.append(scenario_condition)

    if extra_condition is not None:
        conditions.append(extra_condition)

    if not conditions:
        return None
    return ConditionAnd(*conditions)


def select_query(job_name=None, field_names=None, condition=None):
    """Build a SELECT query"""
    quote_it = '"{}"'.format
    if isinstance(field_names, str):
        # Assume user provided a valid string for the SELECT clause
        fields = field_names
    elif field_names:
        # Also retrieve the tags necessary to construct
        # the associated Scenario objects
        mandatory_field_names = {
            '@agent_name',
            '@job_instance_id',
            '@scenario_instance_id',
            '@owner_scenario_instance_id',
            '@suffix'
        }
        mandatory_field_names.update(field_names)
        fields = ','.join(map(quote_it, mandatory_field_names))
    else:
        fields = '*'
    measurement_name = '/.*/' if job_name is None else quote_it(job_name)
    query = 'SELECT {} FROM {}'.format(fields, measurement_name)
    if condition is not None:
        query = '{} WHERE {}'.format(query, condition)
    return query


def measurement_query(job=None, condition=None):
    """Build a SHOW MEASUREMENTS query"""
    query = 'SHOW MEASUREMENTS'
    if job is not None:
        query = '{} WITH MEASUREMENT = "{}"'.format(query, job)
    if condition is not None:
        query = '{} WHERE {}'.format(query, condition)
    return query


def delete_query(job_name=None, scenario=None, agent=None, job_instance=None, suffix=None, condition=None):
    """Build a DELETE query"""
    assert condition is None or condition.is_timestamp
    # Optimize query based on whether or not there is timestamps involved
    query = 'DROP SERIES' if condition is None else 'DELETE'
    query += ' FROM {}'.format('/.*/' if job_name is None else '"{}"'.format(job_name))
    condition = tags_to_condition(scenario, agent, job_instance, suffix, condition)
    if condition is not None:
        query = '{} WHERE {}'.format(query, condition)
    return query


def tag_query(tag_name, job=None, condition=None):
    """Build a SHOW TAG VALUES query"""
    query = 'SHOW TAG VALUES'
    if job is not None:
        query = '{} FROM "{}"'.format(query, job)
    query = '{} WITH KEY = "{}"'.format(query, tag_name)
    if condition:
        query = '{} WHERE {}'.format(query, condition)
    return query


def parse_influx(response):
    """Extract out relevant informations from an InfluxDB's response"""
    for result in response.get('results', []):
        for serie in result.get('series', []):
            with suppress(KeyError):
                name = serie.get('name')
                fields = serie['columns']
                for values in serie['values']:
                    yield name, {f: v for f, v in zip(fields, values) if v is not None}


def parse_statistics(influx_result):
    """Generate `Scenario`s instances from InfluxDB stored data"""
    scenarios = {}  # Cache
    for job_name, statistics in parse_influx(influx_result):
        try:
            timestamp = statistics.pop('time')
            agent = statistics.pop('@agent_name', 'unknown_agent')
            job = int(statistics.pop('@job_instance_id', 0))
            scenario = int(statistics.pop('@scenario_instance_id', 0))
            owner = int(statistics.pop('@owner_scenario_instance_id', 0))
            suffix = statistics.pop('@suffix', None)
        except (KeyError, ValueError):
            pass
        else:
            scenario = get_or_create_scenario(scenario, scenarios)
            owner = get_or_create_scenario(owner, scenarios)
            if owner is not scenario:
                scenario.owner = owner
                owner.sub_scenarios[(scenario.instance_id,)] = scenario
            job = scenario.get_or_create_job(job_name, job, agent)
            stats = job.get_or_create_statistics(suffix)
            stats.add_statistic(timestamp, **statistics)

    yield from scenarios.values()


def parse_orphans(influx_result):
    """Build a `Scenario` instance containing all
    measurements from InfluxDB stored data.
    """
    scenario = Scenario(None)
    for job_name, statistics in parse_influx(influx_result):
        timestamp = statistics.pop('time')
        job = scenario.get_or_create_job(job_name, None, None)
        stats = job.get_or_create_statistics(None)
        stats.add_statistic(timestamp, **statistics)
    return scenario


def line_protocol(job_name, scenario_id, owner_id, agent_name, job_id, suffix, statistics):
    """Generate chuncked bodies for write requests to InfluxDB"""
    if not statistics:
        return

    tags = {
        '@scenario_instance_id': scenario_id,
        '@owner_scenario_instance_id': owner_id,
        '@job_instance_id': job_id,
        '@agent_name': agent_name,
        '@suffix': suffix,
    }

    measurement = [escape_names(job_name, True)]
    measurement.extend(
            # No need to call escape_names on tag as they
            # already fullfil the rules for proper names.
            '{}={}'.format(tag, escape_names(value) if isinstance(value, str) else value)
            for tag, value in tags.items() if value or value == 0)
    header = ','.join(measurement)

    def build_lines_of_data(statistics_chunck):
        for timestamp, data in statistics_chunck:
            fields = ','.join(
                    escape_field(name, value)
                    for name, value in data.items()
                    if value or value == 0)
            yield '{} {} {}'.format(header, fields, timestamp)

    stats_iterator = iter(statistics.items())
    while True:
        chunck = itertools.islice(stats_iterator, LINE_PROTOCOL_CHUNCK_SIZE)
        lines = '\n'.join(build_lines_of_data(chunck))
        if not lines:
            break
        yield lines


###############################
# Fetching and receiving data #
###############################

class InfluxDBCommunicator:
    """Manage network access to an InfluxDB server"""

    TIMEOUT = (2, 3600)  # Requests (connection, data) timeouts in second

    def __init__(self, ip, port=8086, db_name='openbach', precision='ms'):
        """Configure the routes to send/get data to/from InfluxDB"""

        def url_builder(route, time_unit):
            return requests.Request(
                method='GET',
                url='http://{}:{}/{}'.format(ip, port, route),
                params={'db': db_name, time_unit: precision},
            ).prepare().url

        self.writing_URL = url_builder('write', 'precision')
        self.querying_URL = url_builder('query', 'epoch')

    def sql_query(self, query):
        """Send a query to InfluxDB and gather the results"""
        return requests.get(self.querying_URL, params={'q': query}, timeout=self.TIMEOUT).json()

    def data_write(self, data):
        """Send data to InfluxDB so they are stored"""
        return requests.post(self.writing_URL, data.encode(), timeout=self.TIMEOUT)


class InfluxDBConnection(InfluxDBCommunicator):
    def agent_names(self, job=None, scenario=None, job_instance=None, suffix=None):
        """List the available agent names in InfluxDB
        that correspond to the given constraints.
        """
        condition = tags_to_condition(scenario, None, job_instance, suffix)
        response = self.sql_query(tag_query('@agent_name', job, condition))
        return {tag['value'] for _, tag in parse_influx(response)}

    def job_names(self, scenario=None, agent=None, job_instance=None, suffix=None):
        """List the available job names in InfluxDB
        that correspond to the given constraints.
        """
        condition = tags_to_condition(scenario, agent, job_instance, suffix)
        response = self.sql_query(measurement_query(condition=condition))
        return {tag['name'] for _, tag in parse_influx(response)}

    def job_instance_ids(self, job=None, scenario=None, agent=None, suffix=None):
        """List the available job instance IDs in InfluxDB
        that correspond to the given constraints.
        """
        condition = tags_to_condition(scenario, agent, None, suffix)
        response = self.sql_query(tag_query('@job_instance_id', job, condition))
        return {int(tag['value']) for _, tag in parse_influx(response)}

    def scenario_instance_ids(self, job=None, agent=None, job_instance=None, suffix=None):
        """List the available scenario instance IDs in InfluxDB
        that correspond to the given constraints.
        """
        condition = tags_to_condition(None, agent, job_instance, suffix)
        response = self.sql_query(tag_query('@scenario_instance_id', job, condition))
        return {int(tag['value']) for _, tag in parse_influx(response)}

    def timestamps(
            self, job=None, scenario=None, agent=None,
            job_instance=None, suffix=None, condition=None):
        """List the available timestamps in InfluxDB
        that correspond to the given constraints.
        """
        condition = tags_to_condition(scenario, agent, job_instance, suffix)
        response = self.sql_query(select_query(job, condition=condition))
        return {stat['time'] for _, stat in parse_influx(response)}

    def origin(self, job=None, scenario=None, agent=None,
               job_instance=None, suffix=None, condition=None):
        """Retrieve the first timestamp in InfluxDB
        that correspond to the given constraints.
        """
        condition = tags_to_condition(scenario, agent, job_instance, suffix)
        query = '{} LIMIT 1'.format(select_query(job, condition=condition))
        response = self.sql_query(query)
        with suppress(ValueError, KeyError):
            (_, origin_stat), = parse_influx(response)
            return origin_stat['time']

    def suffixes(self, job=None, scenario=None, agent=None, job_instance=None):
        """List the available suffixes in InfluxDB
        that correspond to the given constraints.
        """
        condition = tags_to_condition(scenario, agent, job_instance, None)
        response = self.sql_query(tag_query('@suffix', job, condition))
        return {tag['value'] for _, tag in parse_influx(response)}

    def raw_statistics(
            self, job=None, scenario=None, agent=None, job_instance=None,
            suffix=None, fields=None, condition=None, timestamps=None):
        """Fetch data from InfluxDB that correspond to the given constraints
        and generate values in series.
        """
        if timestamps is not None:
            timestamp_condition = ConditionTimestamp.from_timestamps(timestamps)
            condition = timestamp_condition if condition is None else ConditionAnd(condition, timestamp_condition)
        _condition = tags_to_condition(scenario, agent, job_instance, suffix, condition)
        response = self.sql_query(select_query(job, fields, _condition))
        yield from parse_influx(response)

    def statistics(
            self, job=None, scenario=None, agent=None, job_instance=None,
            suffix=None, fields=None, condition=None, timestamps=None):
        """Fetch data from InfluxDB that correspond to the given constraints
        and generate according `Scenario`s instances.
        """
        if timestamps is not None:
            timestamp_condition = ConditionTimestamp.from_timestamps(timestamps)
            condition = timestamp_condition if condition is None else ConditionAnd(condition, timestamp_condition)
        _condition = tags_to_condition(scenario, agent, job_instance, suffix, condition, subscenarios=True)
        response = self.sql_query(select_query(job, fields, _condition))

        if scenario is not None:
            for scenario_instance in parse_statistics(response):
                if scenario_instance.instance_id == scenario:
                    owner = scenario_instance.owner_instance_id
                    _condition = tags_to_condition(owner, agent, job_instance, suffix, condition, subscenarios=True)
                    response = self.sql_query(select_query(job, fields, _condition))
                    break
        yield from parse_statistics(response)

    def orphans(self, condition=None, timestamps=None):
        """Fetch data from InfluxDB that were not emitted using
        the collect-agent API and build a `Scenario` instance
        without ID holding all such jobs (measurements).
        """
        condition = tags_to_condition('', '', '', '', condition)
        if timestamps is not None:
            timestamp_condition = ConditionTimestamp.from_timestamps(timestamps)
            condition = ConditionAnd(condition, timestamp_condition)
        return parse_orphans(self.sql_query(select_query(None, None, condition)))

    def remove_statistics(
            self, job=None, scenario=None, agent=None,
            job_instance=None, suffix=None, condition=None, timestamps=None):
        """Delete data in InfluxDB that matches the given constraints"""
        if timestamps is not None:
            timestamp_condition = ConditionTimestamp.from_timestamps(timestamps)
            condition = timestamp_condition if condition is None else ConditionAnd(condition, timestamp_condition)
        if condition is None or condition.is_timestamp:
            self.sql_query(delete_query(job, scenario, agent, job_instance, suffix, condition))
            return
        # As InfluxDB cannot delete data based on field
        # content, delete timestamps one by one
        condition = tags_to_condition(scenario, agent, job_instance, suffix, condition)
        response = self.sql_query(select_query(job, [], condition))
        for job_name, statistics in parse_influx(response):
            timestamp = ConditionTimestamp(Operator.Equal, statistics['time'])
            scenario = statistics.get('@scenario_instance_id')
            agent = statistics.get('@agent_name')
            job_instance = statistics.get('@job_instance_id')
            suffix = statistics.get('@suffix')
            # Delete the current timestamp only
            self.sql_query(delete_query(job_name, scenario, agent, job_instance, suffix, timestamp))

    def import_job(self, scenario_id, owner_id, job):
        """Write the data of the given job into InfluxDB"""
        job_name = job.name
        agent_name = job.agent
        job_id = job.instance_id
        for suffix, statistics in job.statistics_data.items():
            # For simplicity, statistics names are stored as 1-tuples
            # keys in statistics_data throughout this package. Extract
            # them here to send them to influx as single strings.
            data_stream = line_protocol(
                    job_name, scenario_id, owner_id, agent_name,
                    job_id, suffix[0], statistics.dated_data)
            for chunck in data_stream:
                response = self.data_write(chunck)
                if __debug__ and response.content:
                    print(response.content, file=sys.stderr)

    def get_field_keys(self):
        """Get the names of the fields from InfluxDB"""
        response = self.sql_query("SHOW FIELD KEYS")
        stats_names = defaultdict(set)
        with suppress(LookupError):
            for result in response['results']:
                for serie in result['series']:
                    job_name = serie['name']
                    stats = (value[0] for value in serie['values'])
                    stats_names[job_name].update(stats)

        return stats_names
