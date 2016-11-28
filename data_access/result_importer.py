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



   @file     result_importer.py
   @brief    
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import requests
import yaml
import json
from datetime import datetime
from .result_data import ScenarioInstanceResult
from .result_filter import Filter


class Importer:
    """ Class that imports Results from files to recreate the Result Structure
    and import it to InfluxDB and ElasticSearch on demand """
    def __init__(self, config_file='config.yml'):
        with open(config_file, 'r') as stream:
            content = yaml.load(stream)
        collector_ip = content['collector_ip']
        influxdb_port = content['influxdb_port']
        database_name = content['database_name']
        elasticsearch_port = content['elasticsearch_port']
        self.influxdb_URL = 'http://{}:{}/write?db={}'.format(
            collector_ip, influxdb_port, database_name)
        self.elasticsearch_URL = 'http://{}:{}/_bulk'.format(
            collector_ip, elasticsearch_port)

    def generate_scenario_instance(self, scenario_file):
        """ Function that generates the scenario instance from a file to the
        result structure """
        with open(scenario_file, 'r') as f:
            scenario_json = f.read()
        scenario_json = json.loads(scenario_json)
        scenario_instance_id = scenario_json.pop('scenario_instance_id')
        scenario_instance = ScenarioInstanceResult(scenario_instance_id)
        agents_json = scenario_json.pop('agents')
        for agent_json in agents_json:
            agent_name = agent_json.pop('name')
            agent = scenario_instance.get_agentresult(agent_name)
            job_instances_json = agent_json.pop('job_instances')
            for job_instance_json in job_instances_json:
                job_instance_id = job_instance_json.pop('job_instance_id')
                job_name = job_instance_json.pop('job_name')
                job_instance = agent.get_jobinstanceresult(job_instance_id,
                                                           job_name)
                logs_json = job_instance_json.pop('logs')
                for log_json in logs_json:
                    job_instance.get_logresult(
                        log_json['_id'], log_json['_index'],
                        log_json['_timestamp'], log_json['_version'],
                        log_json['facility'], log_json['facility_label'],
                        log_json['flag'], log_json['host'], log_json['message'],
                        log_json['pid'], log_json['priority'],
                        log_json['severity'], log_json['severity_label'],
                        log_json['type'])
                statistics_json = job_instance_json.pop('statistics')
                for statistic_json in statistics_json:
                    timestamp = statistic_json.pop('timestamp')
                    values = {}
                    for name, value in statistic_json.items():
                        values[name] = value
                    job_instance.get_statisticresult(timestamp, **values)
        return scenario_instance

    def import_to_collector(self, scenario_instance):
        """ Import the results of the scenario instance in InfluxDB and
        ElasticSearch """
        first_request_to_elasticsearch_done = False
        scenario_instance_id = scenario_instance.scenario_instance_id
        for agent in scenario_instance.agentresults.values():
            agent_name = agent.name
            for job_instance in agent.jobinstanceresults.values():
                job_instance_id = job_instance.job_instance_id
                job_name = job_instance.job_name
                measurement_name = '{}.{}.{}.{}'.format(
                    scenario_instance_id, job_instance_id, agent_name, job_name)
                for statistic in job_instance.statisticresults.values():
                    timestamp = statistic.timestamp
                    values = statistic.values
                    data = ''
                    for name, value in values.items():
                        if data:
                            data = '{},'.format(data)
                        data = '{}{}={}'.format(data, name, value)
                    data = '{} {} {}'.format(measurement_name, data, timestamp)
                    response = requests.post(self.influxdb_URL, data.encode())
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
                        response = requests.post(self.elasticsearch_URL,
                                                 data=content.encode())
                        first_request_to_elasticsearch_done = True
                    response = requests.post(self.elasticsearch_URL,
                                             data=content.encode())
