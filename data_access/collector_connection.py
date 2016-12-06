#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   OpenBACH is a generic testbed able to control/configure multiple
   network/physical entities (under test) and collect data from them. It is
   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
   Agents (one for each network entity that wants to be tested).


   Copyright © 2016 CNES


   This file is part of the OpenBACH testbed.


   OpenBACH is a free software : you can redistribute it and/or modify it under the
   terms of the GNU General Public License as published by the Free Software
   Foundation, either version 3 of the License, or (at your option) any later
   version.

   This program is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
   details.

   You should have received a copy of the GNU General Public License along with
   this program. If not, see http://www.gnu.org/licenses/.



   @file     collector_connection.py
   @brief    
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import requests
import json
import yaml
from datetime import datetime
from .result_filter import (
        OperandStatistic,
        OperandTimestamp,
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
from .result_data import (
        ScenarioInstanceResult,
        StatisticResult,
        LogResult,
)


class CollectorConnection:
    """ Class that makes the requests to the Collector """

    def __init__(self, config_file):
        self.stats = InfluxDBConnection(config_file)
        self.logs = ElasticSearchConnection(config_file)

    def get_scenario_instance_ids(self, agent_name, job_instance_id, job_name,
                                  stat_names, timestamp, condition):
        """ Function that returns all the available scenario_instance_ids in
        InfluxDB and ElasticSearch """
        scenario_instance_ids = self.stats.get_scenario_instance_ids(
            agent_name, job_instance_id, job_name, stat_names, timestamp,
            condition)
        scenario_instance_ids |= self.logs.get_scenario_instance_ids(
            agent_name, job_instance_id, job_name, timestamp)
        return scenario_instance_ids

    def get_agent_names(self, scenario_instance_id, job_instance_id, job_name,
                        stat_names, timestamp, condition):
        """ Function that returns all the avaible agent_names in InfluxDB and
        ElasticSearch """
        agent_names = self.stats.get_agent_names(
            scenario_instance_id, job_instance_id, job_name, stat_names,
            timestamp, condition)
        agent_names |= self.logs.get_agent_names(
            scenario_instance_id, job_instance_id, job_name, timestamp)
        return agent_names

    def get_job_instance_ids(self, scenario_instance_id, agent_name, job_name,
                             stat_names, timestamp, condition):
        """ Function that returns all the available job_instance_ids in InfluxDB
        and ElasticSearch """
        job_instance_ids = self.stats.get_job_instance_ids(
            scenario_instance_id, agent_name, job_name, stat_names,
            timestamp, condition)
        job_instance_ids |= self.logs.get_job_instance_ids(
            scenario_instance_id, agent_name, job_name, timestamp)
        return job_instance_ids

    def get_job_names(self, scenario_instance_id, agent_name, job_instance_id,
                      stat_names, timestamp, condition):
        """ Function that returns all the available job_names in InfluxDB
        and ElasticSearch """
        job_names = self.stats.get_job_names(
            scenario_instance_id, agent_name, job_instance_id, stat_names,
            timestamp, condition)
        job_names |= self.logs.get_job_names(
            scenario_instance_id, agent_name, job_instance_id, timestamp)
        return job_names

    def get_timestamps(self, scenario_instance_id, agent_name, job_instance_id,
                       job_name, stat_names, condition, everything):
        """ Function that returns all the timestamps available in InfluxDB and
        ElasticSearch """
        timestamps = self.stats.get_timestamps(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, condition)
        timestamps |= self.logs.get_timestamps(
            scenario_instance_id, agent_name, job_instance_id, job_name)
        if everything:
            return sorted(timestamps)
        else:
            try:
                return min(timestamps), max(timestamps)
            except ValueError:
                return ()

    def get_scenario_instance_values(self, scenario_instance, agent_name,
                                     job_instance_id, job_name, stat_names,
                                     timestamp, condition):
        """ Function that fills the ScenarioInstanceResult given of the
        available statistics and logs from InfluxDB and ElasticSearch """
        self.stats.get_scenario_instance_values(
            scenario_instance, agent_name, job_instance_id, job_name,
            stat_names, timestamp, condition)
        self.logs.get_scenario_instance_values(
            scenario_instance, agent_name, job_instance_id, job_name, timestamp)

    def get_agent_values(self, agent, job_instance_id, job_name, stat_names,
                         timestamp, condition):
        """ Function that fills the AgentResult given of the
        available statistics and logs from InfluxDB and ElasticSearch """
        self.stats.get_agent_values(
            agent, job_instance_id, job_name, stat_names, timestamp, condition)
        self.logs.get_agent_values(
            agent, job_instance_id, job_name, timestamp)

    def get_job_instance_values(self, job_instance, stat_names, timestamp,
                                condition):
        """ Function that fills the JobInstanceResult given of the
        available statistics and logs from InfluxDB and ElasticSearch """
        self.stats.get_job_instance_values(
            job_instance, stat_names, timestamp, condition)
        self.logs.get_job_instance_values(
            job_instance, timestamp)

    def get_statistic_values(self, statistic, stat_names, condition):
        """ Function that fills the StatisticResult given of the
        available statistics from InfluxDB """
        self.stats.get_statistic_values(
            statistic, stat_names, condition)

    def import_to_collector(self, scenario_instance):
        """ Import the results of the scenario instance in InfluxDB and
        ElasticSearch """
        self.stats.import_to_collector(scenario_instance)
        self.logs.import_to_collector(scenario_instance)

    def del_statistic(self, scenario_instance_id, agent_name, job_instance_id,
                      job_name, stat_names, timestamp, condition):
        """ Function that delete the statistics that match from InfluxDB """
        # TODO See how to delete logs in ElasticSearch
        # For now, the API is new and may change
        # See https://www.elastic.co/guide/en/elasticsearch/reference/5.0/docs-delete-by-query.html
        result = self.stats.del_statistic(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, timestamp, condition)
        return result

    def get_orphan_logs(self, timestamp):
        """ Function that returns the orphan logs from ElasticSearch """
        return self.logs.get_orphan(timestamp)

    def get_orphan_stats(self, timestamp):
        """ Function that returns the orphan statistics from InfluxDB """
        return self.stats.get_orphan(timestamp)


class InfluxDBConnection:
    """ Class taht make the requests to InfluxDB """

    def __init__(self, config_file):
        with open(config_file, 'r') as stream:
            content = yaml.load(stream)
        collector_ip = content['collector_ip']
        influxdb_port = content['influxdb_port']
        database_name = content['database_name']
        epoch = content['epoch']
        self.querying_URL = 'http://{}:{}/query?db={}&epoch={}&q='.format(
            collector_ip, influxdb_port, database_name, epoch)
        self.writing_URL = 'http://{}:{}/write?db={}&precision={}'.format(
            collector_ip, influxdb_port, database_name, epoch)

    def get_query(self, stat_names, timestamp, condition):
        """ Function that constructs the query """
        result = ''
        changed = False
        if stat_names:
            for stat_name in stat_names:
                if changed:
                    result = '{}+and+'.format(result)
                changed = True
                result = '{}"{}"+=~+/./'.format(result, stat_name)
        if condition is not None:
            if changed:
                result = '{}+and+'.format(result)
            changed = True
            result = '{}{}'.format(result, condition)
        if timestamp is not None:
            if changed:
                result = '{}+and+'.format(result)
            changed = True
            try:
                timestamp_down, timestamp_up = timestamp
            except TypeError:
                result = '{}time+=+{}ms'.format(result, timestamp)
            else:
                result = '{}time+<=+{}ms+and+time+>=+{}ms'.format(
                    result, timestamp_up, timestamp_down)
        if changed:
            result = 'where+{}'.format(result)
        return result

    def get_all_measurements(self, scenario_instance_id=None, agent_name=None,
                             job_instance_id=None, job_name=None, stat_names=[],
                             timestamp=None, condition=None):
        """ Function that returns all the available measurements in InfluxDB """
        url = '{}SHOW+MEASUREMENTS'.format(self.querying_URL)
        response = requests.get(url).json()
        values = response['results'][0]['series'][0]['values']
        measurements = set()
        query = self.get_query(stat_names, timestamp, condition)
        for measurement in values:
            try:
                owner_scenario_instance_id, scenario_instance, job_instance, agent_n, job = measurement[0].split('.')
            except ValueError:
                continue
            owner_scenario_instance_id = int(owner_scenario_instance_id)
            scenario_instance = int(scenario_instance)
            job_instance = int(job_instance)
            if scenario_instance_id is not None:
                if (scenario_instance != scenario_instance_id or
                    owner_scenario_instance_id != scenario_instance_id):
                    continue
            if agent_name is not None:
                if agent_n != agent_name:
                    continue
            if job_instance_id is not None:
                if job_instance != job_instance_id:
                    continue
            if job_name is not None:
                if job != job_name:
                    continue
            if query:
                url = '{}select+*+from+"{}"+{}'.format(
                    self.querying_URL, measurement[0], query)
                response = requests.get(url).json()
                try:
                    response['results'][0]['series']
                except KeyError:
                    continue
            measurements.add(measurement[0])
        return measurements

    def get_scenario_instance_ids(self, agent_name, job_instance_id, job_name,
                                  stat_names, timestamp, condition):
        """ Function that returns all the available scenario_instance_ids in
        InfluxDB """
        scenario_instance_ids = set()
        all_measurements = self.get_all_measurements(
            None, agent_name, job_instance_id, job_name,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                _, scenario_instance, _, _, _ = measurement.split('.')
            except ValueError:
                continue
            scenario_instance = int(scenario_instance)
            scenario_instance_ids.add(scenario_instance)
        return scenario_instance_ids

    def get_agent_names(self, scenario_instance_id, job_instance_id, job_name,
                        stat_names, timestamp, condition):
        """ Function that returns all the avaible agent_names in InfluxDB """
        agent_names = set()
        all_measurements = self.get_all_measurements(
            scenario_instance_id, None, job_instance_id, job_name,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                _, _, _, agent_name, _ = measurement.split('.')
            except ValueError:
                continue
            agent_names.add(agent_name)
        return agent_names

    def get_job_instance_ids(self, scenario_instance_id, agent_name, job_name,
                             stat_names, timestamp, condition):
        """ Function that returns all the available job_instance_ids in InfluxDB
        """
        job_instance_ids = set()
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, None, job_name,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                _, _, job_instance_id, _, _ = measurement.split('.')
            except ValueError:
                continue
            job_instance_ids.add(job_instance_id)
        return job_instance_ids

    def get_job_names(self, scenario_instance_id, agent_name, job_instance_id,
                      stat_names, timestamp, condition):
        """ Function that returns all the available job_names in InfluxDB
        """
        job_names = set()
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, None,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                _, _, _, _, job_name = measurement.split('.')
            except ValueError:
                continue
            job_names.add(job_name)
        return job_names

    def get_timestamps(self, scenario_instance_id, agent_name, job_instance_id,
                       job_name, stat_names, condition):
        """ Function that returns all the timestamps available in InfluxDB """
        timestamps = set()
        query = self.get_query(stat_names, None, condition)
        measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, condition)
        for measurement in measurements:
            if stat_names:
                url = '{}select+{}'.format(
                    self.querying_URL, ',+'.join(stat_names))
            else:
                url = '{}select+*'.format(self.querying_URL)
            url = '{}+from+"{}"'.format(url, measurement)
            if query:
                url = '{}{}'.format(url, query)
            response = requests.get(url).json()
            try:
                values = response['results'][0]['series'][0]['values']
            except KeyError:
                continue
            for value in values:
                timestamps.add(value[0])
        return timestamps

    def get_scenario_instance_values(self, scenario_instance, agent_name,
                                     job_instance_id, job_name, stat_names,
                                     timestamp, condition):
        """ Function that fills the ScenarioInstanceResult given of the
        available statistics from InfluxDB """
        scenario_instance_id = scenario_instance.scenario_instance_id
        query = self.get_query(stat_names, timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, condition)
        agent_names = set()
        for measurement in all_measurements:
            try:
                owner_scenario_instance_i, scenario_instance_i, _, agent_n, _ = measurement.split('.')
            except ValueError:
                continue
            owner_scenario_instance_i = int(owner_scenario_instance_i)
            scenario_instance_i = int(scenario_instance_i)
            if scenario_instance_i != scenario_instance_id:
                scenario_instance.sub_scenario_instance_ids.add(
                    scenario_instance_i)
                continue
            elif scenario_instance.owner_scenario_instance_id is None:
                scenario_instance.owner_scenario_instance_id = owner_scenario_instance_i
            agent_names.add(agent_n)
        for agent_n in agent_names:
            agent = scenario_instance.get_agentresult(agent_n)
            measurements = []
            for measurement in all_measurements:
                try:
                    _, _, _, current_agent_n, _ = measurement.split('.')
                    if current_agent_n == agent_n:
                        measurements.append(measurement)
                except ValueError:
                    continue
            for measurement in measurements:
                try:
                    _, _, current_job_instance_id, _, current_job_name = measurement.split('.')
                    current_job_instance_id = int(current_job_instance_id)
                except ValueError:
                    continue
                if stat_names:
                    url = '{}select+{}'.format(
                        self.querying_URL, ',+'.join(stat_names))
                else:
                    url = '{}select+*'.format(self.querying_URL)
                url = '{}+from+"{}"'.format(url, measurement)
                if query:
                    url = '{}{}'.format(url, query)
                response = requests.get(url).json()
                try:
                    current_stat_names = response['results'][0]['series'][0]['columns']
                except KeyError:
                    continue
                stats = {}
                current_index = -1
                for stat_name in current_stat_names:
                    current_index += 1
                    if stat_name in ('time'):
                        continue
                    stats[current_index] = stat_name
                try:
                    values = response['results'][0]['series'][0]['values']
                except KeyError:
                    continue
                job_instance = agent.get_jobinstanceresult(
                    current_job_instance_id, current_job_name)
                for value in values:
                    time = value[0]
                    statistic = {}
                    for index, stat_name in stats.items():
                        statistic[stat_name] = value[index]
                    job_instance.get_statisticresult(time, **statistic)

    def get_agent_values(self, agent, job_instance_id, job_name, stat_names,
                         timestamp, condition):
        """ Function that fills the AgentResult given of the
        available statistics from InfluxDB """
        agent_name = agent.name
        scenario_instance_id = agent.scenario_instance.scenario_instance_id
        query = self.get_query(stat_names, timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, condition)
        measurements = []
        for measurement in all_measurements:
            try:
                _, scenario_instance_i, _, agent_n, _ = measurement.split('.')
                if scenario_instance_i != scenario_instance_id:
                    agent.scenario_instance.sub_scenario_instance_ids.add(
                        scenario_instance_i)
                    continue
                if agent_n == agent_name:
                    measurements.append(measurement)
            except ValueError:
                continue
        for measurement in measurements:
            try:
                _, _, current_job_instance_id, _, current_job_name = measurement.split('.')
                current_job_instance_id = int(current_job_instance_id)
            except ValueError:
                continue
            if stat_names:
                url = '{}select+{}'.format(self.querying_URL, ',+'.join(stat_names))
            else:
                url = '{}select+*'.format(self.querying_URL)
            url = '{}+from+"{}"'.format(url, measurement)
            if query:
                url = '{}{}'.format(url, query)
            response = requests.get(url).json()
            try:
                current_stat_names = response['results'][0]['series'][0]['columns']
            except KeyError:
                return
            stats = {}
            current_index = -1
            for stat_name in current_stat_names:
                current_index += 1
                if stat_name in ('time'):
                    continue
                stats[current_index] = stat_name
            try:
                values = response['results'][0]['series'][0]['values']
            except KeyError:
                return
            job_instance = agent.get_jobinstanceresult(
                current_job_instance_id, current_job_name)
            for value in values:
                time = value[0]
                statistic = {}
                for index, stat_name in stats.items():
                    statistic[stat_name] = value[index]
                job_instance.get_statisticresult(time, **statistic)

    def get_job_instance_values(self, job_instance, stat_names, timestamp,
                                condition):
        """ Function that fills the JobInstanceResult given of the
        available statistics from InfluxDB """
        agent_name = job_instance.agent.name
        job_name = job_instance.job_name
        job_instance_id = job_instance.job_instance_id
        scenario_instance_id = job_instance.agent.scenario_instance.scenario_instance_id
        owner_scenario_instance_id = job_instance.agent.scenario_instance.owner_scenario_instance_id
        query = self.get_query(stat_names, timestamp, condition)
        measurement = '{}.{}.{}.{}.{}'.format(
            owner_scenario_instance_id, scenario_instance_id, job_instance_id,
            agent_name, job_name)
        if stat_names:
            url = '{}select+{}'.format(self.querying_URL, ',+'.join(stat_names))
        else:
            url = '{}select+*'.format(self.querying_URL)
        url = '{}+from+"{}"'.format(url, measurement)
        if query:
            url = '{}{}'.format(url, query)
        response = requests.get(url).json()
        try:
            current_stat_names = response['results'][0]['series'][0]['columns']
        except KeyError:
            return
        stats = {}
        current_index = -1
        for stat_name in current_stat_names:
            current_index += 1
            if stat_name in ('time'):
                continue
            stats[current_index] = stat_name
        try:
            values = response['results'][0]['series'][0]['values']
        except KeyError:
            return
        for value in values:
            time = value[0]
            statistic = {}
            for index, stat_name in stats.items():
                statistic[stat_name] = value[index]
            job_instance.get_statisticresult(time, **statistic)

    def get_statistic_values(self, statistic, stat_names, condition):
        """ Function that fills the StatisticResult given of the
        available statistics from InfluxDB """
        agent_name = statistic.job_instance.agent.name
        job_name = statistic.job_instance.job_name
        job_instance_id = statistic.job_instance.job_instance_id
        scenario_instance_id = statistic.job_instance.agent.scenario_instance.scenario_instance_id
        owner_scenario_instance_id = statistic.job_instance.agent.scenario_instance.owner_scenario_instance_id
        timestamp = statistic.timestamp
        query = self.get_query(stat_names, timestamp, condition)
        measurement = '{}.{}.{}.{}.{}'.format(
            owner_scenario_instance_id, scenario_instance_id, job_instance_id,
            agent_name, job_name)
        if stat_names:
            url = '{}select+{}'.format(self.querying_URL, ',+'.join(stat_names))
        else:
            url = '{}select+*'.format(self.querying_URL)
        url = ('{}+from+"{}"').format(url, measurement)
        if query:
            url = '{}{}'.format(url, query)
        else:
            url = '{}+where'.format(url)
        response = requests.get(url).json()
        try:
            current_stat_names = response['results'][0]['series'][0]['columns']
        except KeyError:
            return
        stats = {}
        current_index = -1
        for stat_name in current_stat_names:
            current_index += 1
            if stat_name in ('time'):
                continue
            stats[current_index] = stat_name
        try:
            values = response['results'][0]['series'][0]['values']
        except KeyError:
            return
        for value in values:
            time = value[0]
            for index, stat_name in stats.items():
                statistic.values[stat_name] = value[index]

    def import_to_collector(self, scenario_instance):
        """ Import the results of the scenario instance in InfluxDB """
        scenario_instance_id = scenario_instance.scenario_instance_id
        owner_scenario_instance_id = scenario_instance.owner_scenario_instance_id
        for agent in scenario_instance.agentresults.values():
            agent_name = agent.name
            for job_instance in agent.jobinstanceresults.values():
                job_instance_id = job_instance.job_instance_id
                job_name = job_instance.job_name
                measurement_name = '{}.{}.{}.{}.{}'.format(
                    owner_scenario_instance_id, scenario_instance_id,
                    job_instance_id, agent_name, job_name)
                for statistic in job_instance.statisticresults.values():
                    timestamp = statistic.timestamp
                    values = statistic.values
                    data = ''
                    for name, value in values.items():
                        if data:
                            data = '{},'.format(data)
                        data = '{}{}={}'.format(data, name, value)
                    data = '{} {} {}'.format(measurement_name, data, timestamp)
                    requests.post(self.writing_URL, data.encode())

    def check_statistic(self, statistic, condition):
        """ Check if a statistic matches the condition """
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

    def filter_scenario_instance(self, scenario_instance, stat_names, timestamp,
                                 condition):
        """ Delete the statistics that match from the ScenarioInstanceResult """
        for agent in scenario_instance.agentresults.values():
            for job_instance in agent.jobinstanceresults.values():
                delete1 = False
                delete_timestamps = []
                if timestamp is None:
                    delete1 = True
                else:
                    try:
                        timestamp_down, timestamp_up = timestamp
                    except ValueError:
                        timestamp_down = timestamp_up = timestamp
                for statistic in job_instance.statisticresults.values():
                    delete2 = False
                    delete3 = False
                    delete4 = False
                    if timestamp is not None:
                        if statistic.timestamp >= timestamp_down:
                            delete2 = True
                        if statistic.timestamp <= timestamp_up:
                            delete2 &= True
                        else:
                            delete2 = False
                    for stat_name in stat_names:
                        if stat_name in statistic.values:
                            delete3 = True
                    if condition is None:
                        delete4 = True
                    else:
                        delete4 = self.check_statistic(statistic, condition)
                    if (delete1 or delete2) and delete3 and delete4:
                        delete_timestamps.append(statistic.timestamp)
                for timestamp in delete_timestamps:
                    del job_instance.statisticresults[timestamp]

    def del_statistic(self, scenario_instance_id, owner_scenario_instance_id,
                      agent_name, job_instance_id, job_name, stat_names,
                      timestamp, condition):
        """ Function that delete the statistics that match from InfluxDB """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id,
                                                   owner_scenario_instance_id)
        self.get_scenario_instance_values(
            scenario_instance, agent_name, job_instance_id, job_name, [],
            None, None)
        measurement = '{}.{}.{}.{}'.format(scenario_instance_id,
                                           job_instance_id, agent_name,
                                           job_name)
        url = '{}drop+measurement+"{}"'.format(self.querying_URL, measurement)
        response = requests.get(url).json()
        self.filter_scenario_instance(scenario_instance, stat_names, timestamp,
                                      condition)
        self.import_to_collector(scenario_instance)
        return True

    def get_orphan(self, timestamp):
        """ Function that returns the orphans statistics from InfluxDB """
        statistics = []
        url = '{}SHOW+MEASUREMENTS'.format(self.querying_URL)
        response = requests.get(url).json()
        values = response['results'][0]['series'][0]['values']
        measurements = set()
        for measurement in values:
            try:
                _, _, _, _, _ = measurement[0].split('.')
                continue
            except ValueError:
                measurements.add(measurement[0])
        query = self.get_query([], timestamp, None)
        for measurement in measurements:
            url = ('{}select+*+from+"{}"').format(self.querying_URL,
                                                  measurement)
            if query:
                url = '{}{}'.format(url, query)
            response = requests.get(url).json()
            try:
                current_stat_names = response['results'][0]['series'][0]['columns']
            except KeyError:
                continue
            stats = {}
            current_index = -1
            for stat_name in current_stat_names:
                current_index += 1
                if stat_name in ('time'):
                    continue
                stats[current_index] = stat_name
            try:
                values = response['results'][0]['series'][0]['values']
            except KeyError:
                continue
            for value in values:
                time = value[0]
                statistic = {}
                for index, stat_name in stats.items():
                    statistic[stat_name] = value[index]
                statistic_result = StatisticResult(time, None, **statistic)
                statistics.append(statistic_result)
        return statistics


class ElasticSearchConnection:
    """ Class that make the requests to ElasticSearch """

    def __init__(self, config_file):
        with open(config_file, 'r') as stream:
            content = yaml.load(stream)
        self.collector_ip = content['collector_ip']
        self.port = content['elasticsearch_port']
        self.querying_URL = 'http://{}:{}/logstash-*/logs/_search'.format(
            self.collector_ip, self.port)
        self.writing_URL = 'http://{}:{}/_bulk'.format(
            self.collector_ip, self.port)

    def get_query(self, scenario_instance_id, agent_name, job_instance_id,
                  job_name, timestamp):
        """ Function that constructs the query """
        query = {'must': [], 'should': []}
        if scenario_instance_id is not None:
            match = {'match': {'owner_scenario_instance_id':
                               scenario_instance_id}}
            query['should'].append(match)
            match = {'match': {'scenario_instance_id': scenario_instance_id}}
            query['should'].append(match)
        if agent_name is not None:
            match = {'match': {'agent_name': agent_name}}
            query['must'].append(match)
        if job_instance_id is not None:
            match = {'match': {'job_instance_id': job_instance_id}}
            query['must'].append(match)
        if job_name is not None:
            match = {'match': {'program': job_name}}
            query['must'].append(match)
        if timestamp is not None:
            try:
                timestamp_down, timestamp_up = timestamp
            except TypeError:
                timestamp_down = timestamp_up = timestamp
            query['filter'] = {
                'bool': {
                    'must': {
                        'range': {
                            '@timestamp': {
                                'gte': timestamp_down,
                                'lte': timestamp_up
                            }
                        }
                    }
                }
            }
        if not query['must']:
            del query['must']
        if not query['should']:
            del query['should']
        if not query:
            query = {'match_all': {}}
        return query

    def get_scenario_instance_ids(self, agent_name, job_instance_id, job_name,
                                  timestamp):
        """ Function that returns all the available scenario_instance_ids in
        ElasticSearch """
        scenario_instance_ids = set()
        query = self.get_query(None, agent_name, job_instance_id, job_name,
                               timestamp)
        if 'match_all' in query:
            query = {'query': query}
        else:
            query = {'query': {'bool': query}}
        url = '{}?fields=scenario_instance_id&scroll=1m'.format(
            self.querying_URL)
        response = requests.post(url, data=json.dumps(query).encode()).json()
        scroll_id = response['_scroll_id']
        try:
            current_hits = response['hits']['hits']
            hits = current_hits
        except KeyError:
            pass
        else:
            while current_hits:
                url = 'http://{}:{}/_search/scroll'
                data = {'scroll': '1m', 'scroll_id': scroll_id}
                url = url.format(self.collector_ip, self.port,
                                 scroll_id)
                response = requests.post(url, data=json.dumps(data)).json()
                scroll_id = response['_scroll_id']
                try:
                    current_hits = response['hits']['hits']
                    hits += current_hits
                except KeyError:
                    pass
            for hit in hits:
                try:
                    scenario_instance_id = hit['fields']['scenario_instance_id'][0]
                except KeyError:
                    pass
                else:
                    try:
                        scenario_instance_id = int(scenario_instance_id)
                    except ValueError:
                        pass
                    else:
                        scenario_instance_ids.add(scenario_instance_id)
        return scenario_instance_ids

    def get_agent_names(self, scenario_instance_id, job_instance_id, job_name,
                        timestamp):
        """ Function that returns all the avaible agent_names in ElasticSearch
        """
        agent_names = set()
        query = self.get_query(scenario_instance_id, None, job_instance_id,
                               job_name, timestamp)
        if 'match_all' in query:
            query = {'query': query}
        else:
            query = {'query': {'bool': query}}
        url = '{}?fields=agent_name&scroll=1m'.format(self.querying_URL)
        response = requests.post(url, data=json.dumps(query)).json()
        scroll_id = response['_scroll_id']
        try:
            current_hits = response['hits']['hits']
            hits = current_hits
        except KeyError:
            pass
        else:
            while current_hits:
                url = 'http://{}:{}/_search/scroll'
                data = {'scroll': '1m', 'scroll_id': scroll_id}
                url = url.format(self.collector_ip, self.port,
                                 scroll_id)
                response = requests.post(url, data=json.dumps(data)).json()
                scroll_id = response['_scroll_id']
                try:
                    current_hits = response['hits']['hits']
                    hits += current_hits
                except KeyError:
                    pass
            for hit in hits:
                try:
                    agent_name = hit['fields']['agent_name'][0]
                except KeyError:
                    pass
                else:
                    agent_names.add(agent_name)
        return agent_names

    def get_job_instance_ids(self, scenario_instance_id, agent_name, job_name,
                             timestamp):
        """ Function that returns all the available job_instance_ids in
        ElasticSearch """
        job_instance_ids = set()
        query = self.get_query(scenario_instance_id, agent_name, None, job_name,
                               timestamp)
        if 'match_all' in query:
            query = {'query': query}
        else:
            query = {'query': {'bool': query}}
        url = '{}?fields=job_instance_id&scroll=1m'.format(self.querying_URL)
        response = requests.post(url, data=json.dumps(query)).json()
        scroll_id = response['_scroll_id']
        try:
            current_hits = response['hits']['hits']
            hits = current_hits
        except KeyError:
            pass
        else:
            while current_hits:
                url = 'http://{}:{}/_search/scroll'
                data = {'scroll': '1m', 'scroll_id': scroll_id}
                url = url.format(self.collector_ip, self.port,
                                 scroll_id)
                response = requests.post(url, data=json.dumps(data)).json()
                scroll_id = response['_scroll_id']
                try:
                    current_hits = response['hits']['hits']
                    hits += current_hits
                except KeyError:
                    pass
            for hit in hits:
                try:
                    job_instance_id = hit['fields']['job_instance_id'][0]
                except KeyError:
                    pass
                else:
                    job_instance_ids.add(job_instance_id)
        return job_instance_ids

    def get_job_names(self, scenario_instance_id, agent_name, job_instance_id,
                      timestamp):
        """ Function that returns all the available job_names in ElasticSearch
        """
        job_names = set()
        query = self.get_query(scenario_instance_id, agent_name,
                               job_instance_id, None, timestamp)
        if 'match_all' in query:
            query = {'query': query}
        else:
            query = {'query': {'bool': query}}
        url = '{}?fields=program&scroll=1m'.format(
            self.querying_URL)
        response = requests.post(url, data=json.dumps(query)).json()
        scroll_id = response['_scroll_id']
        try:
            current_hits = response['hits']['hits']
            hits = current_hits
        except KeyError:
            pass
        else:
            while current_hits:
                url = 'http://{}:{}/_search/scroll'
                data = {'scroll': '1m', 'scroll_id': scroll_id}
                url = url.format(self.collector_ip, self.port,
                                 scroll_id)
                response = requests.post(url, data=json.dumps(data)).json()
                scroll_id = response['_scroll_id']
                try:
                    current_hits = response['hits']['hits']
                    hits += current_hits
                except KeyError:
                    pass
            for hit in hits:
                try:
                    job_name = hit['fields']['program'][0]
                except KeyError:
                    pass
                else:
                    job_names.add(job_name)
        return job_names

    def get_timestamps(self, scenario_instance_id, agent_name, job_instance_id,
                       job_name):
        """ Function that returns all the timestamps available in ElasticSearch
        """
        timestamps = set()
        query = self.get_query(scenario_instance_id, agent_name,
                               job_instance_id, job_name, None)
        query = {'query': query}
        url = '{}?fields=timestamp&scroll=1m'.format(
            self.querying_URL)
        response = requests.post(url, data=json.dumps(query)).json()
        scroll_id = response['_scroll_id']
        try:
            current_hits = response['hits']['hits']
            hits = current_hits
        except KeyError:
            pass
        else:
            while current_hits:
                url = 'http://{}:{}/_search/scroll'
                data = {'scroll': '1m', 'scroll_id': scroll_id}
                url = url.format(self.collector_ip, self.port,
                                 scroll_id)
                response = requests.post(url, data=json.dumps(data)).json()
                scroll_id = response['_scroll_id']
                try:
                    current_hits = response['hits']['hits']
                    hits += current_hits
                except KeyError:
                    pass
            for hit in hits:
                try:
                    _index = hit['_index']
                    time = hit['fields']['timestamp'][0]
                except KeyError:
                    pass
                else:
                    year = int(_index.split('logstash-')[1].split('.')[0])
                    time = datetime.strptime(time, '%b %d %H:%M:%S')
                    timestamp = time.replace(year)
                    timestamp = int(timestamp.timestamp() * 1000)
                    timestamps.add(timestamp)
        return timestamps

    def get_scenario_instance_values(self, scenario_instance, agent_name,
                                     job_instance_id, job_name, timestamp):
        """ Function that fills the ScenarioInstanceResult given of the
        available logs from ElasticSearch """
        scenario_instance_id = scenario_instance.scenario_instance_id
        for log in self.get_logs(scenario_instance_id, agent_name,
                                 job_instance_id, job_name, timestamp):
            log_scenario_instance_id = int(log.pop('scenario_instance_id'))
            if log_scenario_instance_id != scenario_instance_id:
                scenario_instance.sub_scenario_instance_ids.add(
                    log_scenario_instance_id)
                continue
            log_agent_name = log.pop('agent_name')
            log_job_instance_id = int(log.pop('job_instance_id'))
            log_job_name = log.pop('job_name')
            agent = scenario_instance.get_agentresult(log_agent_name)
            job_instance = agent.get_jobinstanceresult(log_job_instance_id,
                                                       log_job_name)
            job_instance.get_logresult(
                log['_id'], log['_index'], log['timestamp'], log['version'],
                log['facility'], log['facility_label'], log['flag'],
                log['host'], log['message'], log['pid'], log['priority'],
                log['severity'], log['severity_label'], log['type'])

    def get_agent_values(self, agent, job_instance_id, job_name, timestamp):
        """ Function that fills the AgentResult given of the
        available logs from ElasticSearch """
        agent_name = agent.name
        scenario_instance_id = agent.scenario_instance.scenario_instance_id
        for log in self.get_logs(scenario_instance_id, agent_name,
                                 job_instance_id, job_name, timestamp):
            log_scenario_instance_id = int(log.pop('scenario_instance_id'))
            log_agent_name = log.pop('agent_name')
            if log_scenario_instance_id != scenario_instance_id:
                agent.scenario_instance.sub_scenario_instance_ids.add(
                    log_scenario_instance_id)
                continue
            log_job_instance_id = int(log.pop('job_instance_id'))
            log_job_name = log.pop('job_name')
            job_instance = agent.get_jobinstanceresult(log_job_instance_id,
                                                       log_job_name)
            job_instance.get_logresult(
                log['_id'], log['_index'], log['timestamp'], log['version'],
                log['facility'], log['facility_label'], log['flag'],
                log['host'], log['message'], log['pid'], log['priority'],
                log['severity'], log['severity_label'], log['type'])

    def get_job_instance_values(self, job_instance, timestamp):
        """ Function that fills the JobInstanceResult given of the
        available logs from ElasticSearch """
        agent_name = job_instance.agent.name
        job_name = job_instance.job_name
        job_instance_id = job_instance.job_instance_id
        scenario_instance_id = job_instance.agent.scenario_instance.scenario_instance_id
        for log in self.get_logs(scenario_instance_id, agent_name,
                                 job_instance_id, job_name, timestamp):
            log_scenario_instance_id = int(log.pop('scenario_instance_id'))
            log_agent_name = log.pop('agent_name')
            log_job_instance_id = int(log.pop('job_instance_id'))
            log_job_name = log.pop('job_name')
            if log_scenario_instance_id != scenario_instance_id:
                job_instance.agent.scenario_instance.sub_scenario_instance_ids.add(
                    log_scenario_instance_id)
                continue
            job_instance.get_logresult(
                log['_id'], log['_index'], log['timestamp'], log['version'],
                log['facility'], log['facility_label'], log['flag'],
                log['host'], log['message'], log['pid'], log['priority'],
                log['severity'], log['severity_label'], log['type'])

    def import_to_collector(self, scenario_instance):
        """ Import the results of the scenario instance in ElasticSearch """
        first_request_to_elasticsearch_done = False
        scenario_instance_id = scenario_instance.scenario_instance_id
        owner_scenario_instance_id = scenario_instance.owner_scenario_instance_id
        for agent in scenario_instance.agentresults.values():
            agent_name = agent.name
            for job_instance in agent.jobinstanceresults.values():
                job_instance_id = job_instance.job_instance_id
                job_name = job_instance.job_name
                for log in job_instance.logresults.values():
                    timestamp = datetime.fromtimestamp(log._timestamp/1000)
                    metadata = {
                        'index': {
                            '_id': log._id,
                            '_index': log._index,
                            '_type': "logs",
                            '_routing': None
                        }
                    }
                    data = {
                        'facility': log.facility,
                        'facility_label': log.facility_label,
                        'flag': log.flag,
                        'host': log.host,
                        'job_instance_id': job_instance_id,
                        'scenario_instance_id': scenario_instance_id,
                        'owner_scenario_instance_id': owner_scenario_instance_id,
                        'logsource': agent_name,
                        'program': job_name,
                        'message': log.message,
                        'pid': log.pid,
                        'priority': log.priority,
                        'severity': log.severity,
                        'severity_label': log.severity_label,
                        '_type': log.type,
                        'timestamp': timestamp.strftime('%b %d %H:%M:%S'),
                        '@timestamp': timestamp.strftime(
                            '%Y-%m-%dT%H:%M:%S.{0:0=3d}Z').format(
                                log._timestamp%1000),
                        '@version': log._version
                    }
                    content = '{}\n{}\n'.format(json.dumps(metadata),
                                                json.dumps(data))
                    if not first_request_to_elasticsearch_done:
                        requests.post(self.writing_URL, data=content.encode())
                        first_request_to_elasticsearch_done = True
                    requests.post(self.writing_URL, data=content.encode())

    def get_orphan(self, timestamp):
        """ Function that returns the orphans logs from ElasticSearch """
        logs = []
        for log in self.get_logs(timestamp=timestamp):
            if 'scenario_instance_id' in log:
                continue
            log_result = LogResult(
                log['_id'], None, log['_index'], log['timestamp'], log['version'],
                log['facility'], log['facility_label'], log['flag'],
                log['host'], log['message'], log['pid'], log['priority'],
                log['severity'], log['severity_label'], log['type'])
            logs.append(log_result)
        return logs

    def get_logs(self, scenario_instance_id=None, agent_name=None,
                 job_instance_id=None, job_name=None, timestamp=None):
        """ Function that do the request to ElasticSearch """
        query = self.get_query(scenario_instance_id, agent_name,
                               job_instance_id, job_name, timestamp)
        if 'match_all' in query:
            query = {'query': query}
        else:
            query = {'query': {'bool': query}}
        url = '{}?scroll=1m'.format(self.querying_URL)
        response = requests.post(url, data=json.dumps(query)).json()
        scroll_id = response['_scroll_id']
        try:
            current_hits = response['hits']['hits']
            hits = current_hits
        except KeyError:
            pass
        else:
            while current_hits:
                url = 'http://{}:{}/_search/scroll'
                data = {'scroll': '1m', 'scroll_id': scroll_id}
                url = url.format(self.collector_ip, self.port,
                                 scroll_id)
                response = requests.post(url, data=json.dumps(data)).json()
                scroll_id = response['_scroll_id']
                try:
                    current_hits = response['hits']['hits']
                    hits += current_hits
                except KeyError:
                    pass
            for hit in hits:
                log = {}
                try:
                    log['_id'] = hit['_id']
                    log['_index'] = hit['_index']
                    timestamp = hit['_source']['timestamp']
                    log['version'] = hit['_source']['@version']
                    log['facility'] = hit['_source']['facility']
                    log['facility_label'] = hit['_source']['facility_label']
                    log['flag'] = hit['_source']['flag']
                    log['host'] = hit['_source']['host']
                    log['message'] = hit['_source']['message']
                    log['pid'] = hit['_source']['pid']
                    log['priority'] = hit['_source']['priority']
                    log['severity'] = hit['_source']['severity']
                    log['severity_label'] = hit['_source']['severity_label']
                    log['type'] = hit['_source']['type']
                except KeyError:
                    continue
                try:
                    log['owner_scenario_instance_id'] = hit['_source']['owner_scenario_instance_id']
                except KeyError:
                    pass
                try:
                    log['scenario_instance_id'] = hit['_source']['scenario_instance_id']
                except KeyError:
                    pass
                try:
                    log['job_instance_id'] = hit['_source']['job_instance_id']
                except KeyError:
                    pass
                try:
                    log['job_name'] = hit['_source']['program']
                except KeyError:
                    pass
                try:
                    log['agent_name'] = hit['_source']['agent_name']
                except KeyError:
                    pass
                year = int(log['_index'].split('logstash-')[1].split('.')[0])
                timestamp = datetime.strptime(timestamp, '%b %d %H:%M:%S')
                timestamp = timestamp.replace(year)
                log['timestamp'] = int(timestamp.timestamp() * 1000)
                yield log
