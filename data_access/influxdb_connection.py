#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016 CNES
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
"""

__author__ = 'Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>'
__credits__ = 'contributions: Mathias ETTINGER'
__all__ = ['InfluxDBConnection']

from collections import defaultdict

import requests

from .result_filter import (
    OperandStatistic,
    OperandValue,
    ConditionAnd,
    ConditionOr,
    ConditionEqual,
    ConditionUpperOrEqual,
    ConditionUpper,
    ConditionNotEqual,
    ConditionBelow,
    ConditionBelowOrEqual,
)
from .result_data import ScenarioInstanceResult, SuffixResult, StatisticResult


def escape_names(name, measurement=False):
    """Escape measurements and fields names as per InfluxDB parsing rules.

    See https://docs.influxdata.com/influxdb/v1.2/
    write_protocols/line_protocol_reference/#special-characters
    for details.
    """
    # Ugly quick hack, replace it with a proper implementation ASAP
    # Use re or whatnot
    escaped = name.replace(' ', '\\ ').replace(',', '\\,')
    if measurement:
        return escaped
    return escaped.replace('=', '\\=')


def escape_field(name, value):
    """Format field names and values as per InfluxDB parsing rules.

    See https://docs.influxdata.com/influxdb/v1.2/
    write_protocols/line_protocol_reference/ for details.
    """
    if isinstance(value, str):
        value = '"{}"'.format(value.replace('"', '\\"'))
    return '{}={}'.format(escape_names(name), value)


class InfluxDBConnection:
    """Manage connection to InfluxDB in order to extract or insert data"""

    def __init__(self, collector_ip, influxdb_port, database_name, epoch='ms'):
        """Configure the connection with request informations"""
        self.writing_URL = requests.Request(
                method='GET',
                url='http://{}:{}/write'.format(collector_ip, influxdb_port),
                params={'db': database_name, 'precision': epoch}).prepare().url
        self.querying_URL = requests.Request(
                method='GET',
                url='http://{}:{}/query'.format(collector_ip, influxdb_port),
                params={'db': database_name, 'epoch': epoch}).prepare().url

    def _request_query(self, sql_query):
        return requests.get(
                self.querying_URL,
                params={'q': sql_query}).json()

    def build_select_template(self, stats_names, timestamp, condition):
        """Construct a SELECT query whose measurement name is missing"""
        clauses = []
        if condition is not None:
            clauses.append(str(condition))
        if timestamp is not None:
            try:
                timestamp_down, timestamp_up = timestamp
            except TypeError:
                clauses.append('time = {}ms'.format(timestamp))
            else:
                clauses.append('time <= {}ms'.format(timestamp_up))
                clauses.append('time >= {}ms'.format(timestamp_down))

        conditions = ' WHERE {}'.format(' AND '.join(clauses)) if clauses else ''
        select = ','.join("{}".format(n) for n in stats_names) if stats_names else '*'
        return 'SELECT {} FROM "{{}}"{}'.format(select, conditions)

    def get_all_measurements(
            self, scenario_instance_id=None,
            agent_name=None, job_instance_id=None,
            job_name=None, suffix_name=None):
        """Return measurements names in InfluxDB that correspond
        to the given constraints.
        """

        regexp = r'\.'.join(
                '.*' if part is None else str(part)
                for part in (None, scenario_instance_id,
                             job_instance_id, agent_name, job_name))
        if suffix_name is not None:
            regexp += r'\.{}'.format(suffix_name)

        query = 'SHOW MEASUREMENTS WITH MEASUREMENT = /{}/'.format(regexp)
        response = self._request_query(query)

        data = response['results'][0]['series'][0]
        assert data['name'] == 'measurements'
        assert data['columns'] == ['name']

        return [measurement[0] for measurement in data['values']]

    def _get_measurement_column(
            self, column, scenario_instance_id, agent_name,
            job_instance_id, job_name, suffix_name):
        """Extract out the nth column from the measurements
        names that correspond to the given query.
        """

        measurements = self.get_all_measurements(
                scenario_instance_id, agent_name,
                job_instance_id, job_name, suffix_name)

        def extract_nth(measurement):
            try:
                nth = measurement.split('.')[column]
            except IndexError:
                return None
            else:
                return nth

        return {extract_nth(m) for m in measurements}

    def get_scenario_instance_ids(
            self, agent_name,
            job_instance_id,
            job_name, suffix_name):
        """Return the available scenarios instance ids in
        InfluxDB that correspond to the given query.
        """
        return self._get_measurement_column(
                1, None, agent_name, job_instance_id,
                job_name, suffix_name)

    def get_agent_names(
            self, scenario_instance_id,
            job_instance_id,
            job_name, suffix_name):
        """Return the avaible agents names in InfluxDB that
        correspond to the given query.
        """
        return self._get_measurement_column(
                3, scenario_instance_id, None,
                job_instance_id, job_name, suffix_name)

    def get_job_instance_ids(
            self, scenario_instance_id,
            agent_name, job_name, suffix_name):
        """Return the available jobs instance ids in InfluxDB that
        correspond to the given query.
        """
        return self._get_measurement_column(
                2, scenario_instance_id, agent_name,
                None, job_name, suffix_name)

    def get_job_names(
            self, scenario_instance_id, agent_name,
            job_instance_id, suffix_name):
        """Return the available jobs names in InfluxDB that
        correspond to the given query.
        """
        return self._get_measurement_column(
                4, scenario_instance_id, agent_name,
                job_instance_id, None, suffix_name)

    def get_suffix_names(self, scenario_instance_id, agent_name,
                         job_instance_id, job_name):
        """Return the available suffixes names in InfluxDB
        that correspond to the given query.
        """
        return self._get_measurement_column(
                4, scenario_instance_id, agent_name,
                job_instance_id, job_name, None)

    def get_timestamps(self, scenario_instance_id, agent_name, job_instance_id,
                       job_name, suffix_name, stat_names, condition):
        """Return the values of timestamps available in InfluxDB
        for the given query.
        """
        timestamps = set()
        query = self.build_select_template(stat_names, None, condition)
        measurements = self.get_all_measurements(
            scenario_instance_id, agent_name,
            job_instance_id, job_name, suffix_name)
        for measurement in measurements:
            response = self._request_query(query.format(measurement))
            try:
                values = response['results'][0]['series'][0]['values']
            except LookupError:
                pass
            else:
                timestamps.update(value[0] for value in values)
        return timestamps

    def _fill_suffix_with_values(self, suffix, sql_query):
        response = self._request_query(sql_query)
        try:
            stats_names = response['results'][0]['series'][0]['columns']
            stats_values = response['results'][0]['series'][0]['values']
        except LookupError:
            return

        time_index = stats_names.index('time')
        for row_value in stats_values:
            statistic = {
                name: value
                for name, value in zip(stats_names, row_value)
                if name != 'time'
            }
            time = row_value[time_index]
            suffix.get_statisticresult(time, **statistic)

    def get_scenario_instance_values(self, scenario_instance, agent_name,
                                     job_instance_id, job_name, suffix_name,
                                     stat_names, timestamp, condition):
        """Fill statistics from InfluxDB corresponding to the given
        query into the provided ScenarioInstanceResult.
        """
        scenario_instance_id = scenario_instance.scenario_instance_id
        query = self.build_select_template(stat_names, timestamp, condition)
        measurements = self.get_all_measurements(
            scenario_instance_id, agent_name,
            job_instance_id, job_name, suffix_name)
        agent_names = defaultdict(list)
        for measurement in measurements:
            owner_id, scenario_id, job_id, agent, job_n, *suffix = measurement.split('.')
            suffix = None if not suffix else suffix[0]
            owner_id = int(owner_id)
            scenario_id = int(scenario_id)
            if scenario_id != scenario_instance_id:
                if scenario_id not in scenario_instance.sub_scenario_instances:
                    sub_scenario_instance = ScenarioInstanceResult(
                            scenario_id, scenario_instance_id)
                    scenario_instance.sub_scenario_instances[scenario_id] = sub_scenario_instance
                continue
            elif scenario_instance.owner_scenario_instance_id is None:
                scenario_instance.owner_scenario_instance_id = owner_id
            assert scenario_instance.owner_scenario_instance_id == owner_id

            agent_names[agent].append((int(job_id), job_n, suffix, measurement))

        for agent_name, measurements in agent_names.items():
            agent = scenario_instance.get_agentresult(agent_name)
            for job_id, job_n, suffix_n, measurement_name in measurements:
                job_instance = agent.get_jobinstanceresult(job_id, job_n)
                suffix = job_instance.get_suffixresult(suffix_n)
                self._fill_suffix_with_values(suffix, query.format(measurement_name))

    def get_agent_values(self, agent, job_instance_id, job_name, suffix_name,
                         stat_names, timestamp, condition):
        """ Function that fills the AgentResult given of the
        available statistics from InfluxDB """
        agent_name = agent.name
        scenario_instance_id = agent.scenario_instance.scenario_instance_id
        query = self.build_select_template(stat_names, timestamp, condition)

        measurements = self.get_all_measurements(
            scenario_instance_id, agent_name,
            job_instance_id, job_name, suffix_name)
        for measurement in measurements:
            _, scenario_id, job_id, _, job, *suffix = measurement.split('.')
            suffix = suffix[0] if suffix else None
            scenario_id = int(scenario_id)
            if scenario_id != scenario_instance_id:
                # Wait... What?
                agent.scenario_instance.sub_scenario_instance_ids.add(scenario_id)
                continue
            job_id = int(job_id)
            job_instance = agent.get_jobinstanceresult(job_id, job)
            suffix_instance = job_instance.get_suffixresult(suffix)
            self._fill_suffix_with_values(suffix_instance, query.format(measurement))

    def get_job_instance_values(
            self, job_instance, suffix_name,
            stat_names, timestamp, condition):
        """ Function that fills the JobInstanceResult given of the
        available statistics from InfluxDB """
        agent_name = job_instance.agent.name
        job_name = job_instance.job_name
        job_instance_id = job_instance.job_instance_id
        scenario_instance_id = job_instance.agent.scenario_instance.scenario_instance_id
        query = self.build_select_template(stat_names, timestamp, condition)
        measurements = self.get_all_measurements(
            scenario_instance_id, agent_name,
            job_instance_id, job_name, suffix_name)
        for measurement in measurements:
            _, scenario_id, _, _, _, *suffix = measurement.split('.')
            suffix = suffix[0] if suffix else None
            scenario_id = int(scenario_id)
            if scenario_id != scenario_instance_id:
                # Dude, WTF?
                job_instance.agent.scenario_instance.sub_scenario_instance_ids.add(scenario_id)
                continue
            suffix_instance = job_instance.get_suffixresult(suffix)
            self._fill_suffix_with_values(suffix_instance, query.format(measurement))

    def get_suffix_values(self, suffix, stat_names, timestamp, condition):
        """ Function that fills the JobInstanceResult given of the
        available suffix from InfluxDB """
        suffix_name = suffix.name
        agent_name = suffix.job_instance.agent.name
        job_name = suffix.job_instance.job_name
        job_instance_id = suffix.job_instance.job_instance_id
        scenario_instance_id = suffix.job_instance.agent.scenario_instance.scenario_instance_id
        owner_scenario_instance_id = suffix.job_instance.agent.scenario_instance.owner_scenario_instance_id
        if owner_scenario_instance_id is None:
            owner_scenario_instance_id = scenario_instance_id

        query = self.build_select_template(stat_names, timestamp, condition)
        measurement = '{}.{}.{}.{}.{}'.format(
            owner_scenario_instance_id, scenario_instance_id,
            job_instance_id, agent_name, job_name)
        if suffix_name is not None:
            measurement = '{}.{}'.format(measurement, suffix_name)

        self._fill_suffix_with_values(suffix, query.format(measurement))

    def get_statistic_values(self, statistic, stat_names, condition):
        """ Function that fills the StatisticResult given of the
        available statistics from InfluxDB """
        agent_name = statistic.suffix.job_instance.agent.name
        suffix_name = statistic.suffix.name
        job_name = statistic.suffix.job_instance.job_name
        job_instance_id = statistic.suffix.job_instance.job_instance_id
        scenario_instance_id = statistic.suffix.job_instance.agent.scenario_instance.scenario_instance_id
        owner_scenario_instance_id = statistic.suffix.job_instance.agent.scenario_instance.owner_scenario_instance_id
        if owner_scenario_instance_id is None:
            owner_scenario_instance_id = scenario_instance_id
        timestamp = statistic.timestamp
        query = self.build_select_template(stat_names, timestamp, condition)
        measurement = '{}.{}.{}.{}.{}'.format(
            owner_scenario_instance_id, scenario_instance_id, job_instance_id,
            agent_name, job_name)
        if suffix_name is not None:
            measurement = '{}.{}'.format(measurement, suffix_name)
        response = self._request_query(query.format(measurement))
        try:
            stats_names = response['results'][0]['series'][0]['columns']
            stats_values = response['results'][0]['series'][0]['values']
        except LookupError:
            return

        assert len(stats_values) < 2
        for row_value in stats_values:
            stats = {
                name: value
                for name, value in zip(stats_names, row_value)
                if name != 'time'
            }
            statistic.values.update(stats)

    def export_to_collector(self, scenario_instance):
        """ Import the results of the scenario instance in InfluxDB """
        scenario_instance_id = scenario_instance.scenario_instance_id
        owner_scenario_instance_id = scenario_instance.owner_scenario_instance_id
        for agent in scenario_instance.agentresults.values():
            agent_name = agent.name
            for job_instance in agent.jobinstanceresults.values():
                job_instance_id = job_instance.job_instance_id
                job_name = job_instance.job_name
                measurement_name = escape_names('{}.{}.{}.{}.{}'.format(
                    owner_scenario_instance_id, scenario_instance_id,
                    job_instance_id, agent_name, job_name), True)
                for statistic in job_instance.statisticresults.values():
                    timestamp = statistic.timestamp
                    data = ','.join(escape_field(n, v) for n, v in statistic.values.items())
                    body = '{} {} {}'.format(measurement_name, data, timestamp)
                    requests.post(self.writing_URL, body.encode())
        for sub_scenario_instance in scenario_instance.sub_scenario_instances.values():
            self.export_to_collector(sub_scenario_instance)

    def check_statistic(self, statistic, condition):
        """Check if a statistic matches the condition"""
        if isinstance(condition, ConditionAnd):
            delete = self.check_statistic(statistic, condition.condition1)
            delete &= self.check_statistic(statistic, condition.condition2)
        elif isinstance(condition, ConditionOr):
            delete = self.check_statistic(statistic, condition.condition1)
            delete |= self.check_statistic(statistic, condition.condition2)
        else:
            operand1 = condition.operand1
            operand2 = condition.operand2
            if isinstance(operand1, OperandStatistic):
                try:
                    value1 = statistic.values[operand1.name]
                except KeyError:
                    return False
            elif isinstance(operand1, OperandValue):
                value1 = operand1.value
            if isinstance(operand2, OperandStatistic):
                try:
                    value2 = statistic.values[operand1.name]
                except KeyError:
                    return False
            elif isinstance(operand2, OperandValue):
                value2 = operand2.value
            if isinstance(condition, ConditionEqual):
                return value1 == value2
            elif isinstance(condition, ConditionNotEqual):
                return value1 != value2
            elif isinstance(condition, ConditionUpperOrEqual):
                return value1 >= value2
            elif isinstance(condition, ConditionUpper):
                return value1 > value2
            elif isinstance(condition, ConditionBelowOrEqual):
                return value1 <= value2
            elif isinstance(condition, ConditionBelow):
                return value1 < value2
        return delete

    def filter_scenario_instance(self, scenario_instance, stat_names, timestamp, condition):
        """Delete the statistics from the ScenarioInstanceResult that
        matches the given conditions.
        """
        try:
            timestamp_down, timestamp_up = timestamp
        except (TypeError, ValueError):
            timestamp_down = timestamp_up = timestamp

        for agent in scenario_instance.agentresults.values():
            for job_instance in agent.jobinstanceresults.values():
                delete_timestamps = []
                for statistic in job_instance.statisticresults.values():
                    time = statistic.timestamp
                    if timestamp is None or timestamp_down <= time <= timestamp_up:
                        for stat_name in stat_names:
                            if stat_name in statistic.values:
                                if condition is None or self.check_statistic(statistic, condition):
                                    delete_timestamps.append(time)
                for time in delete_timestamps:
                    del job_instance.statisticresults[time]

    def del_statistic(self, owner_scenario_instance_id, scenario_instance_id,
                      agent_name, job_instance_id, job_name, suffix_name,
                      stat_names, timestamp, condition):
        """Delete the statistics that match from InfluxDB"""
        scenario_instance = ScenarioInstanceResult(scenario_instance_id,
                                                   owner_scenario_instance_id)
        self.get_scenario_instance_values(
            scenario_instance, agent_name, job_instance_id, job_name,
            suffix_name, [], None, None)
        measurement = '{}.{}.{}.{}.{}'.format(
            owner_scenario_instance_id, scenario_instance_id,
            job_instance_id, agent_name, job_name)
        measurements = (
            measurement if name is None else '{}.{}'.format(measurement, name)
            for name in scenario_instance.agentresults[agent_name]
                        .jobinstanceresults[job_instance_id].suffixresults
        )
        for measurement in measurements:
            self._request_query('DROP MEASUREMENT "{}"'.format(measurement))
        self.filter_scenario_instance(scenario_instance, stat_names, timestamp, condition)
        self.export_to_collector(scenario_instance)

    def get_orphan(self, timestamp):
        """ Function that returns the orphans statistics from InfluxDB """
        suffix = SuffixResult(None, None)
        response = self._request_query('SHOW MEASUREMENTS')
        measurements = response['results'][0]['series'][0]['values']
        query = self.build_select_template([], timestamp, None)
        for measurement, in measurements:
            if 5 != len(measurement.split('.')) != 6:
                self._fill_suffix_with_values(suffix, query.format(measurement))

        # Disassociate stats from temporary suffix
        return [
            StatisticResult(stat.timestamp, None, **stat.values)
            for stat in suffix.statisticresult_iter
        ]
