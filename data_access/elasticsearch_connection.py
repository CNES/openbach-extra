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



   @file     elasticsearch_connection.py
   @brief
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import requests
import json
import yaml
from datetime import datetime
from .result_data import  LogResult


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
