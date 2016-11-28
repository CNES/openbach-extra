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



   @file     result_requester.py
   @brief    
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import requests
import json
import yaml
from datetime import datetime
from .result_data import ScenarioInstanceResult
from .result_filter import Filter


class Requester:
    """ Class that makes the requests to InfluxDB and ElasticSearch """
    def __init__(self, config_file='config.yml'):
        with open(config_file, 'r') as stream:
            content = yaml.load(stream)
        self.collector_ip = content['collector_ip']
        influxdb_port = content['influxdb_port']
        database_name = content['database_name']
        epoch = content['epoch']
        self.elasticsearch_port = content['elasticsearch_port']
        self.influxdb_URL = 'http://{}:{}/query?db={}&epoch={}&q='.format(
            self.collector_ip, influxdb_port, database_name, epoch)
        self.elasticsearch_URL = 'http://{}:{}/logstash-*/logs/_search'.format(
            self.collector_ip, self.elasticsearch_port)

    def get_all_measurements(self, scenario_instance_id=None, agent_name=None,
                             job_instance_id=None, job_name=None, stat_names=[],
                             timestamp=None, condition=None):
        """ Function that returns all the available measurements in InfluxDB """
        request_filter = Filter(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, timestamp, condition)
        url = '{}SHOW+MEASUREMENTS'.format(self.influxdb_URL)
        response = requests.get(url).json()
        values = response['results'][0]['series'][0]['values']
        measurements = set()
        for measurement in values:
            try:
                scenario_instance, job_instance, agent_n, job = measurement[0].split('.')
            except ValueError:
                continue
            scenario_instance = int(scenario_instance)
            job_instance = int(job_instance)
            if scenario_instance_id is not None:
                if scenario_instance != scenario_instance_id:
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
            if stat_names or condition is not None or timestamp is not None:
                url = '{}select+*+from+"{}"+{}'.format(
                    self.influxdb_URL, measurement[0], request_filter)
                response = requests.get(url).json()
                try:
                    response['results'][0]['series']
                except KeyError:
                    continue
            measurements.add(measurement[0])
        return measurements

    def get_scenario_instance_ids(self, agent_name=None, job_instance_id=None,
                                  job_name=None, stat_names=[], timestamp=None,
                                  condition=None):
        """ Function that returns all the available scenario_instance_ids in
        InfluxDB and ElasticSearch """
        request_filter = Filter(
            None, agent_name, job_instance_id, job_name,
            stat_names, timestamp, condition)
        scenario_instance_ids = set()
        all_measurements = self.get_all_measurements(
            None, agent_name, job_instance_id, job_name,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                scenario_instance, _, _, _ = measurement.split('.')
            except ValueError:
                continue
            scenario_instance = int(scenario_instance)
            scenario_instance_ids.add(scenario_instance)
        query = request_filter.get_query()
        url = '{}?fields=scenario_instance_id&scroll=1m'.format(
            self.elasticsearch_URL)
        if query:
            url = '{}{}'.format(url, query)
        response = requests.get(url).json()
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
                url = url.format(self.collector_ip, self.elasticsearch_port,
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

    def get_agent_names(self, scenario_instance_id=None,
                        job_instance_id=None, job_name=None, stat_names=[],
                        timestamp=None, condition=None):
        """ Function that returns all the avaible agent_names in InfluxDB and
        ElasticSearch """
        request_filter = Filter(
            scenario_instance_id, None, job_instance_id, job_name,
            stat_names, timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, None, job_instance_id, job_name,
            stat_names, condition)
        agent_names = set()
        for measurement in all_measurements:
            try:
                _, _, agent_name, _ = measurement.split('.')
            except ValueError:
                continue
            agent_names.add(agent_name)
        query = request_filter.get_query()
        url = '{}?fields=agent_name&scroll=1m'.format(
            self.elasticsearch_URL)
        if query:
            url = '{}{}'.format(url, query)
        response = requests.get(url).json()
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
                url = url.format(self.collector_ip, self.elasticsearch_port,
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

    def get_job_instance_ids(self, scenario_instance_id=None, agent_name=None,
                             job_name=None, stat_names=[], timestamp=None, 
                             condition=None):
        """ Function that returns all the available job_instance_ids in InfluxDB
        """
        job_instance_ids = set()
        request_filter = Filter(
            scenario_instance_id, agent_name, None, job_name,
            stat_names, timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, None, job_name,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                _, job_instance_id, _, _ = measurement.split('.')
            except ValueError:
                continue
            job_instance_ids.add(job_instance_id)
        query = request_filter.get_query()
        url = '{}?fields=job_instance_id&scroll=1m'.format(
            self.elasticsearch_URL)
        if query:
            url = '{}{}'.format(url, query)
        response = requests.get(url).json()
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
                url = url.format(self.collector_ip, self.elasticsearch_port,
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

    def get_job_names(self, scenario_instance_id=None, agent_name=None,
                      job_instance_id=None, stat_names=[], timestamp=None,
                      condition=None):
        """ Function that returns all the available job_names in InfluxDB
        """
        job_names = set()
        request_filter = Filter(
            scenario_instance_id, agent_name, job_instance_id, None,
            stat_names, timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, None,
            stat_names, condition)
        for measurement in all_measurements:
            try:
                _, _, _, job_name = measurement.split('.')
            except ValueError:
                continue
            job_names.add(job_name)
        query = request_filter.get_query()
        url = '{}?fields=program&scroll=1m'.format(
            self.elasticsearch_URL)
        if query:
            url = '{}{}'.format(url, query)
        response = requests.get(url).json()
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
                url = url.format(self.collector_ip, self.elasticsearch_port,
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

    def get_timestamps(self, scenario_instance_id=None, agent_name=None,
                      job_instance_id=None, job_name=None, stat_names=[],
                      condition=None, everything=False):
        """ Function that returns all the timestamps available in InfluxDB and
        ElasticSearch """
        request_filter = Filter(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, None, condition)
        measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, condition)
        timestamps = set()
        for measurement in measurements:
            if stat_names:
                url = '{}select+{}'.format(
                    self.influxdb_URL, ',+'.join(stat_names))
            else:
                url = '{}select+*'.format(self.influxdb_URL)
            url = '{}+from+"{}"'.format(url, measurement)
            if condition is not None:
                url = '{}{}'.format(url, request_filter)
            response = requests.get(url).json()
            try:
                values = response['results'][0]['series'][0]['values']
            except KeyError:
                continue
            for value in values:
                timestamps.add(value[0])
        query = request_filter.get_query()
        url = '{}?fields=timestamp&scroll=1m'.format(
            self.elasticsearch_URL)
        if query:
            url = '{}{}'.format(url, query)
        response = requests.get(url).json()
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
                url = url.format(self.collector_ip, self.elasticsearch_port,
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
        if everything:
            return sorted(timestamps)
        else:
            try:
                return min(timestamps), max(timestamps)
            except ValueError:
                return ()

    def _get_scenario_instance_values(self, scenario_instance, agent_name,
                                      job_instance_id, job_name, stat_names,
                                      timestamp, condition):
        """ Function that fills the ScenarioInstanceResult given of the
        available statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance_id = scenario_instance.scenario_instance_id
        request_filter = Filter(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, condition)
        agent_names = set()
        for measurement in all_measurements:
            try:
                _, _, agent_n, _ = measurement.split('.')
            except ValueError:
                continue
            agent_names.add(agent_n)
        for agent_n in agent_names:
            agent = scenario_instance.get_agentresult(agent_n)
            measurements = []
            for measurement in all_measurements:
                try:
                    _, _, current_agent_n, _ = measurement.split('.')
                    if current_agent_n == agent_n:
                        measurements.append(measurement)
                except ValueError:
                    continue
            for measurement in measurements:
                try:
                    _, current_job_instance_id, _, current_job_name = measurement.split('.')
                    current_job_instance_id = int(current_job_instance_id)
                except ValueError:
                    continue
                if stat_names:
                    url = '{}select+{}'.format(
                        self.influxdb_URL, ',+'.join(stat_names))
                else:
                    url = '{}select+*'.format(self.influxdb_URL)
                url = '{}+from+"{}"'.format(url, measurement)
                if condition is not None or timestamp is not None:
                    url = '{}{}'.format(url, request_filter)
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
                    serie = {}
                    for index, stat_name in stats.items():
                        serie[stat_name] = value[index]
                    job_instance.get_serieresult(time, **serie)
        for log in self.get_logs(scenario_instance_id, agent_name,
                                 job_instance_id, job_name, condition,
                                 timestamp):
            log_scenario_instance_id = int(log.pop('scenario_instance_id'))
            if log_scenario_instance_id != scenario_instance_id:
                #TODO See how to inform of this error
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

    def get_scenario_instance_values(self, scenario_instance_id,
                                     agent_name=None, job_instance_id=None,
                                     job_name=None, stat_names=[],
                                     condition=None, timestamp=None):
        """ Function that returns a ScenarioInstanceResult full of the available
        statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id)
        self._get_scenario_instance_values(scenario_instance, agent_name,
                                           job_instance_id, job_name,
                                           stat_names, condition, timestamp)
        return scenario_instance

    def _get_agent_values(self, agent, job_instance_id, job_name, stat_names,
                          timestamp, condition):
        """ Function that fills the AgentResult given of the
        available statistics and logs from InfluxDB and ElasticSearch """
        agent_name = agent.name
        scenario_instance_id = agent.scenario_instance.scenario_instance_id
        request_filter = Filter(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, timestamp, condition)
        all_measurements = self.get_all_measurements(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, condition)
        measurements = []
        for measurement in all_measurements:
            try:
                _, _, agent_n, _ = measurement.split('.')
                if agent_n == agent_name:
                    measurements.append(measurement)
            except ValueError:
                continue
        for measurement in measurements:
            try:
                _, current_job_instance_id, _, current_job_name = measurement.split('.')
                current_job_instance_id = int(current_job_instance_id)
            except ValueError:
                continue
            if stat_names:
                url = '{}select+{}'.format(self.influxdb_URL, ',+'.join(stat_names))
            else:
                url = '{}select+*'.format(self.influxdb_URL)
            url = '{}+from+"{}"'.format(url, measurement)
            if condition is not None or timestamp is not None:
                url = '{}{}'.format(url, request_filter)
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
                serie = {}
                for index, stat_name in stats.items():
                    serie[stat_name] = value[index]
                job_instance.get_serieresult(time, **serie)
        for log in self.get_logs(scenario_instance_id, agent_name,
                                 job_instance_id, job_name, condition,
                                 timestamp):
            log_scenario_instance_id = int(log.pop('scenario_instance_id'))
            log_agent_name = log.pop('agent_name')
            if not (log_scenario_instance_id == scenario_instance_id and
                    log_agent_name == agent_name):
                #TODO See how to inform of this error
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

    def get_agent_values(self, scenario_instance_id, agent_name,
                         job_instance_id=None, job_name=None, stat_names=[],
                         condition=None, timestamp=None):
        """ Function that returns a AgentResult full of the available statistics
        and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id)
        agent = scenario_instance.get_agentresult(agent_name)
        self._get_agent_values(agent, job_instance_id, job_name, stat_names,
                               condition, timestamp)
        return agent

    def _get_job_instance_values(self, job_instance, stat_names, timestamp,
                                 condition):
        """ Function that fills the JobInstanceResult given of the
        available statistics and logs from InfluxDB and ElasticSearch """
        agent_name = job_instance.agent.name
        job_name = job_instance.job_name
        job_instance_id = job_instance.job_instance_id
        scenario_instance_id = job_instance.agent.scenario_instance.scenario_instance_id
        request_filter = Filter(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, timestamp, condition)
        measurement = '{}.{}.{}.{}'.format(scenario_instance_id,
                                           job_instance_id, agent_name,
                                           job_name)
        if stat_names:
            url = '{}select+{}'.format(self.influxdb_URL, ',+'.join(stat_names))
        else:
            url = '{}select+*'.format(self.influxdb_URL)
        url = '{}+from+"{}"'.format(url, measurement)
        if condition is not None or timestamp is not None:
            url = '{}{}'.format(url, request_filter)
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
            serie = {}
            for index, statistic in stats.items():
                serie[stat_name] = value[index]
            job_instance.get_serieresult(time, **serie)
        for log in self.get_logs(scenario_instance_id, agent_name,
                                 job_instance_id, job_name, condition,
                                 timestamp):
            log_scenario_instance_id = int(log.pop('scenario_instance_id'))
            log_agent_name = log.pop('agent_name')
            log_job_instance_id = int(log.pop('job_instance_id'))
            log_job_name = log.pop('job_name')
            if not (log_scenario_instance_id == scenario_instance_id and
                    log_agent_name == agent_name and log_job_instance_id ==
                    job_instance_id and log_job_name == job_name):
                #TODO See how to inform of this error
                continue
            job_instance.get_logresult(
                log['_id'], log['_index'], log['timestamp'], log['version'],
                log['facility'], log['facility_label'], log['flag'],
                log['host'], log['message'], log['pid'], log['priority'],
                log['severity'], log['severity_label'], log['type'])

    def get_job_instance_values(self, scenario_instance_id, agent_name,
                                job_instance_id, job_name, stat_names=[],
                                condition=None, timestamp=None):
        """ Function that returns a JobInstanceResult full of the
        available statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id)
        agent = scenario_instance.get_agentresult(agent_name)
        job_instance = agent.get_jobinstanceresult(job_instance_id, job_name)
        self._get_job_instance_values(job_instance, stat_names, condition,
                                      timestamp)
        return job_instance

    def _get_serie_values(self, serie, stat_names, timestamp, condition):
        """ Function that fills the SerieResult given of the
        available statistics and logs from InfluxDB """
        agent_name = serie.job_instance.agent.name
        job_name = serie.job_instance.job_name
        job_instance_id = serie.job_instance.job_instance_id
        scenario_instance_id = serie.job_instance.agent.scenario_instance.scenario_instance_id
        timestamp = serie.timestamp
        request_filter = Filter(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, timestamp, condition)
        measurement = '{}.{}.{}.{}'.format(scenario_instance_id,
                                           job_instance_id, agent_name,
                                           job_name)
        if stat_names:
            url = '{}select+{}'.format(self.influxdb_URL, ',+'.join(stat_names))
        else:
            url = '{}select+*'.format(self.influxdb_URL)
        url = ('{}+from+"{}"').format(url, measurement)
        if condition is not None or timestamp is not None:
            url = '{}{}+and'.format(url, request_filter)
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
                serie.statistics[stat_name] = value[index]

    def get_serie_values(self, scenario_instance_id, agent_name,
                         job_instance_id, job_name, timestamp, stat_names=[],
                         condition=None):
        """ Function that returns the StatisticResult full of the
        available statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id)
        agent = scenario_instance.get_agentresult(agent_name)
        job_instance = agent.get_jobinstanceresult(job_instance_id, job_name)
        serie = job_instance.get_serieresult(timestamp)
        self._get_serie_values(serie, stat_names, condition)
        return serie

    def get_logs(self, scenario_instance_id=None, agent_name=None,
                 job_instance_id=None, job_name=None, timestamp=None,
                 condition=None):
        """ Function that do the request to ElasticSearch """
        request_filter = Filter(
            scenario_instance_id, agent_name, job_instance_id, job_name, [],
            timestamp, condition)
        query = request_filter.get_query()
        data = {'query': {'bool': query}}
        url = '{}?scroll=1m'.format(self.elasticsearch_URL)
        response = requests.post(url, data=json.dumps(data)).json()
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
                url = url.format(self.collector_ip, self.elasticsearch_port,
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
