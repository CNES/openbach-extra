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



   @file     influxdb_connection.py
   @brief
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import requests
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
)


class InfluxDBConnection:
    """ Class taht make the requests to InfluxDB """

    def __init__(self, collector_ip, influxdb_port, database_name, epoch='ms'):
        self.querying_URL = 'http://{}:{}/query?db={}&epoch={}&q='.format(
            collector_ip, influxdb_port, database_name, epoch)
        self.writing_URL = 'http://{}:{}/write?db={}&precision={}'.format(
            collector_ip, influxdb_port, database_name, epoch)

    def get_query(self, timestamp, condition):
        """ Function that constructs the query """
        result = ''
        changed = False
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
                             job_instance_id=None, job_name=None,
                             suffix_name=None, stat_names=[], timestamp=None,
                             condition=None):
        """ Function that returns all the available measurements in InfluxDB """
        url = '{}SHOW+MEASUREMENTS'.format(self.querying_URL)
        response = requests.get(url).json()
        values = response['results'][0]['series'][0]['values']
        measurements = set()
        query = self.get_query(timestamp, condition)
        for measurement in values:
            try:
                owner_scenario_instance_id, scenario_instance, job_instance, agent_n, job, suffix_n = measurement[0].split('.')
            except ValueError:
                try:
                    owner_scenario_instance_id, scenario_instance, job_instance, agent_n, job = measurement[0].split('.')
                    suffix_n = None
                except ValueError:
                    continue
            owner_scenario_instance_id = int(owner_scenario_instance_id)
            scenario_instance = int(scenario_instance)
            job_instance = int(job_instance)
            if scenario_instance_id is not None:
                if (scenario_instance != scenario_instance_id and
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
            if suffix_name is not None:
                if suffix_n != suffix_name:
                    continue
            url = '+from+"' + measurement[0] + '"'
            if query:
                url += '+' + query
            if query or stat_names:
                url = '{}select+{}{}'.format(self.querying_URL, ','.join(stat_names), url)
                response = requests.get(url).json()
                try:
                    response['results'][0]['series']
                except KeyError:
                    continue
            measurements.add(measurement[0])
        return measurements

    def get_scenario_instance_ids(self, agent_name, job_instance_id, job_name,
                                  suffix_name, stat_names, timestamp,
                                  condition):
        """ Function that returns all the available scenario_instance_ids in
        InfluxDB """
        scenario_instance_ids = set()
        all_measurements = self.get_all_measurements(
            None, agent_name, job_instance_id, job_name, suffix_name,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                _, scenario_instance, _, _, _, _ = measurement.split('.')
            except ValueError:
                try:
                    _, scenario_instance, _, _, _ = measurement.split('.')
                except ValueError:
                    continue
            scenario_instance = int(scenario_instance)
            scenario_instance_ids.add(scenario_instance)
        return scenario_instance_ids

    def get_agent_names(self, scenario_instance_id, job_instance_id, job_name,
                        suffix_name, stat_names, timestamp, condition):
        """ Function that returns all the avaible agent_names in InfluxDB """
        agent_names = set()
        all_measurements = self.get_all_measurements(
            scenario_instance_id, None, job_instance_id, job_name, suffix_name,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                _, _, _, agent_name, _, _ = measurement.split('.')
            except ValueError:
                try:
                    _, _, _, agent_name, _ = measurement.split('.')
                except ValueError:
                    continue
            agent_names.add(agent_name)
        return agent_names

    def get_job_instance_ids(self, scenario_instance_id, agent_name, job_name,
                             suffix_name, stat_names, timestamp, condition):
        """ Function that returns all the available job_instance_ids in InfluxDB
        """
        job_instance_ids = set()
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, None, job_name, suffix_name,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                _, _, job_instance_id, _, _, _ = measurement.split('.')
            except ValueError:
                try:
                    _, _, job_instance_id, _, _ = measurement.split('.')
                except ValueError:
                    continue
            job_instance_ids.add(job_instance_id)
        return job_instance_ids

    def get_job_names(self, scenario_instance_id, agent_name, job_instance_id,
                      suffix_name, stat_names, timestamp, condition):
        """ Function that returns all the available job_names in InfluxDB
        """
        job_names = set()
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, None,
            suffix_name, stat_names, condition)
        for measurement in all_measurements:
            try:
                _, _, _, _, job_name, _ = measurement.split('.')
            except ValueError:
                try:
                    _, _, _, _, job_name = measurement.split('.')
                except ValueError:
                    continue
            job_names.add(job_name)
        return job_names

    def get_suffix_names(self, scenario_instance_id=None, agent_name=None,
                         job_instance_id=None, job_name=None, stat_names=[],
                         timestamp=None, condition=None):
        """ Function that returns all the available suffix_names in InfluxDB """
        suffix_names = set()
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            None, stat_names, condition)
        for measurement in all_measurements:
            try:
                _, _, _, _, _, suffix_name = measurement.split('.')
            except ValueError:
                try:
                    _, _, _, _, _ = measurement.split('.')
                    suffix_name = None
                except ValueError:
                    continue
            suffix_names.add(suffix_name)
        return suffix_names

    def get_timestamps(self, scenario_instance_id, agent_name, job_instance_id,
                       job_name, suffix_name, stat_names, condition):
        """ Function that returns all the timestamps available in InfluxDB """
        timestamps = set()
        query = self.get_query(None, condition)
        measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            suffix_name, stat_names, condition)
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
                                     job_instance_id, job_name, suffix_name,
                                     stat_names, timestamp, condition):
        """ Function that fills the ScenarioInstanceResult given of the
        available statistics from InfluxDB """
        scenario_instance_id = scenario_instance.scenario_instance_id
        query = self.get_query(timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            suffix_name, stat_names, condition)
        agent_names = set()
        measurements_scenario = []
        for measurement in all_measurements:
            try:
                owner_scenario_instance_i, scenario_instance_i, _, agent_n, _, _ = measurement.split('.')
            except ValueError:
                try:
                    owner_scenario_instance_i, scenario_instance_i, _, agent_n, _ = measurement.split('.')
                except ValueError:
                    continue
            owner_scenario_instance_i = int(owner_scenario_instance_i)
            scenario_instance_i = int(scenario_instance_i)
            if scenario_instance_i != scenario_instance_id:
                if scenario_instance_i not in scenario_instance.sub_scenario_instances:
                    sub_scenario_instance = ScenarioInstanceResult(
                        scenario_instance_i, scenario_instance_id)
                    scenario_instance.sub_scenario_instances[scenario_instance_i] = sub_scenario_instance
                continue
            elif scenario_instance.owner_scenario_instance_id is None:
                scenario_instance.owner_scenario_instance_id = owner_scenario_instance_i
            agent_names.add(agent_n)
            measurements_scenario.append(measurement)
        for agent_n in agent_names:
            agent = scenario_instance.get_agentresult(agent_n)
            measurements = []
            for measurement in measurements_scenario:
                try:
                    _, _, _, current_agent_n, _ = measurement.split('.')
                    if current_agent_n == agent_n:
                        measurements.append(measurement)
                except ValueError:
                    continue
            for measurement in measurements:
                try:
                    _, _, current_job_instance_id, _, current_job_name, suffix_n = measurement.split('.')
                except ValueError:
                    try:
                        _, _, current_job_instance_id, _, current_job_name = measurement.split('.')
                        suffix_n = None
                    except ValueError:
                        continue
                current_job_instance_id = int(current_job_instance_id)
                job_instance = agent.get_jobinstanceresult(
                    current_job_instance_id, current_job_name)
                suffix = job_instance.get_suffixresult(suffix_n)
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
                for value in values:
                    time = value[0]
                    statistic = {}
                    for index, stat_name in stats.items():
                        if value[index] is not None:
                            statistic[stat_name] = value[index]
                    suffix.get_statisticresult(time, **statistic)

    def get_agent_values(self, agent, job_instance_id, job_name, suffix_name,
                         stat_names, timestamp, condition):
        """ Function that fills the AgentResult given of the
        available statistics from InfluxDB """
        agent_name = agent.name
        scenario_instance_id = agent.scenario_instance.scenario_instance_id
        query = self.get_query(timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            suffix_name, stat_names, condition)
        measurements = []
        for measurement in all_measurements:
            try:
                _, scenario_instance_i, _, _, _, _ = measurement.split('.')
            except ValueError:
                try:
                    _, scenario_instance_i, _, _, _ = measurement.split('.')
                except ValueError:
                    continue
            scenario_instance_i = int(scenario_instance_i)
            if scenario_instance_i != scenario_instance_id:
                agent.scenario_instance.sub_scenario_instance_ids.add(
                    scenario_instance_i)
                continue
            measurements.append(measurement)
        for measurement in measurements:
            try:
                _, _, current_job_instance_id, _, current_job_name, suffix_n = measurement.split('.')
            except ValueError:
                try:
                    _, _, current_job_instance_id, _, current_job_name = measurement.split('.')
                    suffix_n = None
                except ValueError:
                    continue
            current_job_instance_id = int(current_job_instance_id)
            job_instance = agent.get_jobinstanceresult(
                current_job_instance_id, current_job_name)
            suffix = job_instance.get_suffixresult(suffix_n)
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
                    if value[index] is not None:
                        statistic[stat_name] = value[index]
                suffix.get_statisticresult(time, **statistic)

    def get_job_instance_values(self, job_instance, suffix_name, stat_names,
                                timestamp, condition):
        """ Function that fills the JobInstanceResult given of the
        available statistics from InfluxDB """
        agent_name = job_instance.agent.name
        job_name = job_instance.job_name
        job_instance_id = job_instance.job_instance_id
        scenario_instance_id = job_instance.agent.scenario_instance.scenario_instance_id
        query = self.get_query(timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            suffix_name, stat_names, condition)
        measurements = []
        for measurement in all_measurements:
            try:
                _, scenario_instance_i, _, _, _, _ = measurement.split('.')
            except ValueError:
                try:
                    _, scenario_instance_i, _, _, _ = measurement.split('.')
                except ValueError:
                    continue
            scenario_instance_i = int(scenario_instance_i)
            if scenario_instance_i != scenario_instance_id:
                job_instance.agent.scenario_instance.sub_scenario_instance_ids.add(
                    scenario_instance_i)
                continue
            measurements.append(measurement)
        for measurement in measurements:
            try:
                _, _, _, _, _, suffix_n = measurement.split('.')
            except ValueError:
                suffix_n = None
            suffix = job_instance.get_suffixresult(suffix_n)
            if stat_names:
                url = '{}select+{}'.format(self.querying_URL, ',+'.join(
                    stat_names))
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
                    if value[index] is not None:
                        statistic[stat_name] = value[index]
                suffix.get_statisticresult(time, **statistic)

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
        query = self.get_query(timestamp, condition)
        measurement = '{}.{}.{}.{}.{}'.format(
            owner_scenario_instance_id, scenario_instance_id, job_instance_id,
            agent_name, job_name)
        if suffix_name is not None:
            measurement += '.' + suffix_name
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
                if value[index] is not None:
                    statistic[stat_name] = value[index]
            suffix.get_statisticresult(time, **statistic)

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
        query = self.get_query(timestamp, condition)
        measurement = '{}.{}.{}.{}.{}'.format(
            owner_scenario_instance_id, scenario_instance_id, job_instance_id,
            agent_name, job_name)
        if suffix_name is not None:
            measurement += '.' + suffix_name
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

    def export_to_collector(self, scenario_instance):
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
        for sub_scenario_instance in scenario_instance.sub_scenario_instances.values():
            self.export_to_collector(sub_scenario_instance)

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

    def del_statistic(self, owner_scenario_instance_id, scenario_instance_id,
                      agent_name, job_instance_id, job_name, suffix_name,
                      stat_names, timestamp, condition):
        """ Function that delete the statistics that match from InfluxDB """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id,
                                                   owner_scenario_instance_id)
        self.get_scenario_instance_values(
            scenario_instance, agent_name, job_instance_id, job_name,
            suffix_name, [], None, None)
        measurement = '{}.{}.{}.{}.{}'.format(
            owner_scenario_instance_id, scenario_instance_id, job_instance_id,
            agent_name, job_name)
        measurements = []
        if suffix_name is not None:
            measurement += '.' + suffix_name
            measurements.append(measurement)
        else:
            for suffix_name in scenario_instance.agentresults[agent_name].jobinstanceresults[job_instance_id].suffixresults:
                if suffix_name is None:
                    measurements.append(measurement)
                else:
                    m = measurement + '.' + suffix_name
                    measurements.append(m)
        for measurement in measurements:
            url = '{}drop+measurement+"{}"'.format(
                self.querying_URL, measurement)
            response = requests.get(url).json()
        self.filter_scenario_instance(scenario_instance, stat_names, timestamp,
                                      condition)
        self.export_to_collector(scenario_instance)
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
                try:
                    _, _, _, _, _, _ = measurement[0].split('.')
                    continue
                except ValueError:
                    measurements.add(measurement[0])
        query = self.get_query(timestamp, None)
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
