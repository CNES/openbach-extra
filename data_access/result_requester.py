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
from .collector_connection import CollectorConnection


class Requester:
    """ Class that makes the requests to InfluxDB and ElasticSearch """
    def __init__(self, config_file='config.yml'):
        self.collector_connection = CollectorConnection(config_file)

    def get_scenario_instance_ids(self, agent_name=None, job_instance_id=None,
                                  job_name=None, stat_names=[], timestamp=None,
                                  condition=None):
        """ Function that returns all the available scenario_instance_ids in
        InfluxDB and ElasticSearch """
        return self.collector_connection.get_scenario_instance_ids(
            agent_name, job_instance_id, job_name, stat_names, timestamp,
            condition)

    def get_agent_names(self, scenario_instance_id=None,
                        job_instance_id=None, job_name=None, stat_names=[],
                        timestamp=None, condition=None):
        """ Function that returns all the avaible agent_names in InfluxDB and
        ElasticSearch """
        return self.collector_connection.get_agent_names(
            scenario_instance_id, job_instance_id, job_name, stat_names,
            timestamp, condition)

    def get_job_instance_ids(self, scenario_instance_id=None, agent_name=None,
                             job_name=None, stat_names=[], timestamp=None, 
                             condition=None):
        """ Function that returns all the available job_instance_ids in InfluxDB
        and ElasticSearch """
        return self.collector_connection.get_job_instance_ids(
            scenario_instance_id, agent_name, job_name, stat_names,
            timestamp, condition)

    def get_job_names(self, scenario_instance_id=None, agent_name=None,
                      job_instance_id=None, stat_names=[], timestamp=None,
                      condition=None):
        """ Function that returns all the available job_names in InfluxDB
        and ElasticSearch """
        return self.collector_connection.get_job_names(
            scenario_instance_id, agent_name, job_instance_id, stat_names,
            timestamp, condition)

    def get_timestamps(self, scenario_instance_id=None, agent_name=None,
                      job_instance_id=None, job_name=None, stat_names=[],
                      condition=None, everything=False):
        """ Function that returns all the timestamps available in InfluxDB and
        ElasticSearch """
        return self.collector_connection.get_timestamps(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            stat_names, condition, everything)

    def get_scenario_instance_values(self, scenario_instance_id,
                                     agent_name=None, job_instance_id=None,
                                     job_name=None, stat_names=[],
                                     condition=None, timestamp=None):
        """ Function that returns a ScenarioInstanceResult full of the available
        statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id)
        self.collector_connection.get_scenario_instance_values(
            scenario_instance, agent_name, job_instance_id, job_name,
            stat_names, timestamp, condition)
        return scenario_instance

    def get_agent_values(self, scenario_instance_id, agent_name,
                         job_instance_id=None, job_name=None, stat_names=[],
                         condition=None, timestamp=None):
        """ Function that returns a AgentResult full of the available statistics
        and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id)
        agent = scenario_instance.get_agentresult(agent_name)
        self.collector_connection.get_agent_values(
            agent, job_instance_id, job_name, stat_names, condition, timestamp)
        return agent

    def get_job_instance_values(self, scenario_instance_id, agent_name,
                                job_instance_id, job_name, stat_names=[],
                                condition=None, timestamp=None):
        """ Function that returns a JobInstanceResult full of the
        available statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id)
        agent = scenario_instance.get_agentresult(agent_name)
        job_instance = agent.get_jobinstanceresult(job_instance_id, job_name)
        self.collector_connection.get_job_instance_values(
            job_instance, stat_names, condition, timestamp)
        return job_instance

    def get_statistic_values(self, scenario_instance_id, agent_name,
                             job_instance_id, job_name, timestamp,
                             stat_names=[], condition=None):
        """ Function that returns the StatisticResult full of the
        available statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id)
        agent = scenario_instance.get_agentresult(agent_name)
        job_instance = agent.get_jobinstanceresult(job_instance_id, job_name)
        statistic = job_instance.get_statisticresult(timestamp)
        self.collector_connection.get_statistic_values(
            statistic, stat_names, condition)
        return statistic
