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
from .collector_connection import CollectorConnection


class Importer:
    """ Class that imports Results from files to recreate the Result Structure
    and import it to InfluxDB and ElasticSearch on demand """
    def __init__(self, config_file='config.yml'):
        self.collector_connection = CollectorConnection(config_file)

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
        self.collector_connection.import_to_collector(scenario_instance)
