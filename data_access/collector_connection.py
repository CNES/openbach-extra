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


import json
from .result_data import ScenarioInstanceResult
from .influxdb_connection import InfluxDBConnection
from .elasticsearch_connection import ElasticSearchConnection


def read_scenario(filename):
    """Generate a ScenarioInstanceResult instance from a file.

    The file should contain the equivalent of a JSON
    dump of the dictionary returned by the `json` property
    of the corresponding ScenarioInstanceResult instance.
    """

    with open(filename) as f:
        scenario_json = json.load(f)
    return ScenarioInstanceResult.load(scenario_json)


class CollectorConnection:
    """ Class that makes the requests to the Collector """

    def __init__(self, collector_ip,
                 elasticsearch_port=9200,
                 influxdb_port=8086,
                 database_name='openbach',
                 epoch='ms'):
        self.stats = InfluxDBConnection(collector_ip, influxdb_port, database_name, epoch)
        self.logs = ElasticSearchConnection(collector_ip, elasticsearch_port)

    def get_scenario_instance_ids(
            self, agent_name=None, job_instance_id=None,
            job_name=None, suffix_name=None, timestamp=None):
        """ Function that returns all the available scenario_instance_ids in
        InfluxDB and ElasticSearch """
        scenario_instance_ids = self.stats.get_scenario_instance_ids(
            agent_name, job_instance_id, job_name, suffix_name)
        scenario_instance_ids |= self.logs.get_scenario_instance_ids(
            agent_name, job_instance_id, job_name, timestamp)
        return scenario_instance_ids

    def get_agent_names(
            self, scenario_instance_id=None, job_instance_id=None,
            job_name=None, suffix_name=None, timestamp=None):
        """ Function that returns all the avaible agent_names in InfluxDB and
        ElasticSearch """
        agent_names = self.stats.get_agent_names(
            scenario_instance_id, job_instance_id, job_name, suffix_name)
        agent_names |= self.logs.get_agent_names(
            scenario_instance_id, job_instance_id, job_name, timestamp)
        return agent_names

    def get_job_instance_ids(
            self, scenario_instance_id=None, agent_name=None,
            job_name=None, suffix_name=None, timestamp=None):
        """ Function that returns all the available job_instance_ids in InfluxDB
        and ElasticSearch """
        job_instance_ids = self.stats.get_job_instance_ids(
            scenario_instance_id, agent_name, job_name, suffix_name)
        job_instance_ids |= self.logs.get_job_instance_ids(
            scenario_instance_id, agent_name, job_name, timestamp)
        return job_instance_ids

    def get_job_names(
            self, scenario_instance_id=None, agent_name=None,
            job_instance_id=None, suffix_name=None, timestamp=None):
        """ Function that returns all the available job_names in InfluxDB
        and ElasticSearch """
        job_names = self.stats.get_job_names(
            scenario_instance_id, agent_name, job_instance_id, suffix_name)
        job_names |= self.logs.get_job_names(
            scenario_instance_id, agent_name, job_instance_id, timestamp)
        return job_names

    def get_suffix_names(
            self, scenario_instance_id=None, agent_name=None,
            job_instance_id=None, job_name=None):
        """ Function that returns all the available suffix_names in InfluxDB """
        return self.stats.get_suffix_names(
            scenario_instance_id, agent_name, job_instance_id, job_name)

    def get_timestamps(self, scenario_instance_id=None, agent_name=None,
                       job_instance_id=None, job_name=None, suffix_name=None,
                       stat_names=[], condition=None, everything=False):
        """ Function that returns all the timestamps available in InfluxDB and
        ElasticSearch """
        timestamps = self.stats.get_timestamps(
            scenario_instance_id, agent_name, job_instance_id, job_name,
            suffix_name, stat_names, condition)
        timestamps |= self.logs.get_timestamps(
            scenario_instance_id, agent_name, job_instance_id, job_name)
        if everything:
            return sorted(timestamps)
        else:
            try:
                return min(timestamps), max(timestamps)
            except ValueError:
                return ()

    def _get_scenario_instance_values(self, scenario_instance, agent_name,
                                      job_instance_id, job_name, suffix_name,
                                      stat_names, timestamp, condition):
        """ Function that fills the ScenarioInstanceResult given of the
        available statistics and logs from InfluxDB and ElasticSearch """
        self.stats.get_scenario_instance_values(
            scenario_instance, agent_name, job_instance_id, job_name,
            suffix_name, stat_names, timestamp, condition)
        self.logs.get_scenario_instance_values(
            scenario_instance, agent_name, job_instance_id, job_name, timestamp)
        for sub_scenario_instance in scenario_instance.sub_scenario_instances.values():
            self._get_scenario_instance_values(
                sub_scenario_instance, agent_name, job_instance_id, job_name,
                suffix_name, stat_names, timestamp, condition)

    def get_scenario_instance_values(self, scenario_instance_id,
                                     agent_name=None, job_instance_id=None,
                                     job_name=None, suffix_name=None, 
                                     stat_names=[], timestamp=None,
                                     condition=None):
        """ Function that returns a ScenarioInstanceResult full of the available
        statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id, None)
        self._get_scenario_instance_values(
            scenario_instance, agent_name, job_instance_id, job_name,
            suffix_name, stat_names, timestamp, condition)
        return scenario_instance

    def _get_agent_values(self, agent, job_instance_id, job_name, suffix_name,
                          stat_names, timestamp, condition):
        """ Function that fills the AgentResult given of the
        available statistics and logs from InfluxDB and ElasticSearch """
        self.stats.get_agent_values(
            agent, job_instance_id, job_name, suffix_name, stat_names,
            timestamp, condition)
        self.logs.get_agent_values(
            agent, job_instance_id, job_name, timestamp)

    def get_agent_values(self, scenario_instance_id, agent_name,
                         job_instance_id=None, job_name=None, suffix_name=None,
                         stat_names=[], timestamp=None, condition=None):
        """ Function that returns a AgentResult full of the available statistics
        and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id, None)
        agent = scenario_instance.get_agentresult(agent_name)
        self._get_agent_values(
            agent, job_instance_id, job_name, suffix_name, stat_names,
            condition, timestamp)
        return agent

    def _get_job_instance_values(self, job_instance, suffix_name, stat_names,
                                 timestamp, condition):
        """ Function that fills the JobInstanceResult given of the
        available statistics and logs from InfluxDB and ElasticSearch """
        self.stats.get_job_instance_values(
            job_instance, suffix_name, stat_names, timestamp, condition)
        self.logs.get_job_instance_values(job_instance, timestamp)

    def get_job_instance_values(self, scenario_instance_id, agent_name,
                                job_instance_id, job_name, suffix_name=None,
                                stat_names=[], timestamp=None, condition=None):
        """ Function that returns a JobInstanceResult full of the
        available statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id, None)
        agent = scenario_instance.get_agentresult(agent_name)
        job_instance = agent.get_jobinstanceresult(job_instance_id, job_name)
        self._get_job_instance_values(
            job_instance, suffix_name, stat_names, condition, timestamp)
        return job_instance

    def _get_suffix_values(self, suffix, stat_names, timestamp, condition):
        """ Function that fills the JobInstanceResult given of the
        available suffix from InfluxDB """
        self.stats.get_suffix_values( suffix, stat_names, timestamp, condition)

    def get_suffix_values(self, scenario_instance_id, agent_name,
                          job_instance_id, job_name, suffix_name,
                          stat_names=[], timestamp=None, condition=None):
        """ Function that fills the JobInstanceResult given of the
        available suffix from InfluxDB """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id, None)
        agent = scenario_instance.get_agentresult(agent_name)
        job_instance = agent.get_jobinstanceresult(job_instance_id, job_name)
        suffix = job_instance.get_suffixresult(suffix_name)
        self._get_suffix_values(suffix, stat_names, timestamp, condition)
        return suffix

    def _get_statistic_values(self, statistic, stat_names, condition):
        """ Function that fills the StatisticResult given of the
        available statistics from InfluxDB """
        self.stats.get_statistic_values(statistic, stat_names, condition)

    def get_statistic_values(self, scenario_instance_id, agent_name,
                             job_instance_id, job_name, suffix_name, timestamp,
                             stat_names=[], condition=None):
        """ Function that returns the StatisticResult full of the
        available statistics and logs from InfluxDB and ElasticSearch """
        scenario_instance = ScenarioInstanceResult(scenario_instance_id, None)
        agent = scenario_instance.get_agentresult(agent_name)
        job_instance = agent.get_jobinstanceresult(job_instance_id, job_name)
        suffix = job_instance.get_suffixresult(suffix_name)
        statistic = suffix.get_statisticresult(timestamp)
        self._get_statistic_values(statistic, stat_names, condition)
        return statistic

    def export_to_collector(self, scenario_instance):
        """ Import the results of the scenario instance in InfluxDB and
        ElasticSearch """
        self.stats.export_to_collector(scenario_instance)
        self.logs.export_to_collector(scenario_instance)

    def del_scenario_instance(self, owner_scenario_instance_id,
                              scenario_instance_id, agent_name=None,
                              job_instance_id=None, job_name=None,
                              suffix_name=None, stat_names=[], timestamp=None,
                              condition=None):
        """ Function that deletes a Scenario Instance from InfluxDB """
        if agent_name is None:
            agent_names = self.get_agent_names(
                scenario_instance_id, job_instance_id, job_name, suffix_name,
                [], timestamp, None)
            success = True
            for agent_n in agent_names:
                success &= self.del_agent(
                    owner_scenario_instance_id, scenario_instance_id, agent_n,
                    job_instance_id, job_name, suffix_name, stat_names,
                    timestamp, condition)
        else:
            success = self.del_agent(
                owner_scenario_instance_id, scenario_instance_id, agent_name,
                job_instance_id, job_name, suffix_name, stat_names, timestamp,
                condition)
        return success

    def del_agent(self, owner_scenario_instance_id, scenario_instance_id,
                  agent_name, job_instance_id=None, job_name=None,
                  suffix_name=None, stat_names=[], timestamp=None,
                  condition=None):
        """ Function that deletes an Agent from InfluxDB """
        if job_instance_id is None:
            job_instance_ids = self.get_job_instance_ids(
                scenario_instance_id, agent_name, job_name, suffix_name, [],
                timestamp, None)
            success = True
            for job_instance_i in job_instance_ids:
                job_instance_i = int(job_instance_i)
                if job_name is None:
                    job_names = self.get_job_names(
                        scenario_instance_id, agent_name, job_instance_i,
                        suffix_name, [], timestamp, None)
                    for job_n in job_names:
                        success &= self.del_job_instance(
                            owner_scenario_instance_id, scenario_instance_id,
                            agent_name, job_instance_i, job_n, suffix_name, 
                            stat_names, timestamp, condition)
                else:
                    success &= self.del_job_instance(
                        owner_scenario_instance_id, scenario_instance_id,
                        agent_name, job_instance_i, job_name, suffix_name,
                        stat_names, timestamp, condition)
        elif job_name is None:
            job_names = self.get_job_names(
                scenario_instance_id, agent_name, job_instance_id, suffix_name,
                [], timestamp, None)
            success = True
            for job_n in job_names:
                success &= self.del_job_instance(
                    owner_scenario_instance_id, scenario_instance_id,
                    agent_name, job_instance_id, job_n, suffix_name, stat_names,
                    timestamp, condition)
        else:
            success = self.del_job_instance(
                owner_scenario_instance_id, scenario_instance_id, agent_name,
                job_instance_id, job_name, suffix_name, stat_names, timestamp,
                condition)
        return success

    def del_job_instance(self, owner_scenario_instance_id, scenario_instance_id,
                         agent_name, job_instance_id, job_name,
                         suffix_name=None, stat_names=[],
                         timestamp=None, condition=None):
        """ Function that deletes a Job Instance from InfluxDB """
        if suffix_name is None:
            suffix_names = self.get_suffix_names(
                scenario_instance_id, agent_name, job_instance_id, job_name, [],
                timestamp, None)
            success = True
            for suffix_n in suffix_names:
                success &= self.del_suffix(
                    owner_scenario_instance_id, scenario_instance_id,
                    agent_name, job_instance_id, job_name, suffix_n, stat_names,
                    timestamp, condition)
        else:
            success = self.del_suffix(
                owner_scenario_instance_id, scenario_instance_id, agent_name,
                job_instance_id, job_name, suffix_name, stat_names, timestamp,
                condition)
        return success

    def del_suffix(self, owner_scenario_instance_id, scenario_instance_id,
                   agent_name, job_instance_id, job_name, suffix_name,
                   stat_names=[], timestamp=None, condition=None):
        """ Function that deletes a Suffix from InfluxDB """
        # TODO See how to delete logs in ElasticSearch
        # For now, the API is new and may change
        # See https://www.elastic.co/guide/en/elasticsearch/reference/5.0/docs-delete-by-query.html
        return self.del_statistic(
            owner_scenario_instance_id, scenario_instance_id, agent_name,
            job_instance_id, job_name, suffix_name, stat_names, timestamp,
            condition)

    def del_statistic(self, owner_scenario_instance_id, scenario_instance_id,
                      agent_name, job_instance_id, job_name, suffix_name,
                      stat_names, timestamp, condition):
        """ Function that delete the statistics that match from InfluxDB """
        result = self.stats.del_statistic(
            owner_scenario_instance_id, scenario_instance_id, agent_name,
            job_instance_id, job_name, suffix_name, stat_names, timestamp,
            condition)
        return result

    def get_orphan_logs(self, timestamp):
        """ Function that returns the orphan logs from ElasticSearch """
        return self.logs.get_orphan(timestamp)

    def get_orphan_stats(self, timestamp):
        """ Function that returns the orphan statistics from InfluxDB """
        return self.stats.get_orphan(timestamp)
