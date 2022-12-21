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

__author__ = 'Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>'
__credits__ = 'contributions: Mathias ETTINGER'
__all__ = ['CollectorConnection']

from contextlib import suppress

from .influxdb_tools import InfluxDBConnection
from .elasticsearch_tools import ElasticSearchConnection
from .result_data import extract_jobs, get_or_create_scenario


class CollectorConnection:
    """Wrapper around the two supported databases: InfluxDB and ElasticSearch.

    This class gather data from both databases and merges them into a single
    `Scenario` instance.
    """

    def __init__(self, collector_ip,
                 elasticsearch_port=9200,
                 influxdb_port=8086,
                 database_name='openbach',
                 epoch='ms'):
        self.influxdb = InfluxDBConnection(collector_ip, influxdb_port, database_name, epoch)
        self.elasticsearch = ElasticSearchConnection(collector_ip, elasticsearch_port)

    def agent_names(
            self, job_name=None, scenario_instance_id=None,
            job_instance_id=None, suffix=None, timestamps=None):
        """List all the avaible agent names in InfluxDB and ElasticSearch"""
        return self.influxdb.agent_names(
                job_name, scenario_instance_id, job_instance_id, suffix,
        ) | self.elasticsearch.agent_names(
                job_name, scenario_instance_id, job_instance_id, timestamps,
        )

    def job_names(
            self, scenario_instance_id=None, agent_name=None,
            job_instance_id=None, suffix=None, timestamps=None):
        """List all the avaible job names in InfluxDB and ElasticSearch"""
        return self.influxdb.job_names(
                scenario_instance_id, agent_name, job_instance_id, suffix,
        ) | self.elasticsearch.job_names(
                scenario_instance_id, agent_name, job_instance_id, timestamps,
        )

    def job_instance_ids(
            self, job_name=None, scenario_instance_id=None,
            agent_name=None, suffix=None, timestamps=None):
        """List all the avaible job instance IDs in InfluxDB and ElasticSearch"""
        return self.influxdb.job_instance_ids(
                job_name, scenario_instance_id, agent_name, suffix,
        ) | self.elasticsearch.job_instance_ids(
                job_name, scenario_instance_id, agent_name, timestamps,
        )

    def scenario_instance_ids(
            self, job_name=None, agent_name=None,
            job_instance_id=None, suffix=None, timestamps=None):
        """List all the avaible scenario instance IDs in InfluxDB and ElasticSearch"""
        return self.influxdb.scenario_instance_ids(
                job_name, agent_name, job_instance_id, suffix,
        ) | self.elasticsearch.scenario_instance_ids(
                job_name, agent_name, job_instance_id, timestamps,
        )

    def timestamps(
            self, job_name=None, scenario_instance_id=None,
            agent_name=None, job_instance_id=None, suffix=None,
            condition=None, only_bounds=True):
        """List all the avaible timestamps in InfluxDB and ElasticSearch
        that correspond to the given constraints.

        Sort them before returning the list. Optionally return only
        a couple containing the minimum and maximum values.
        """
        timestamps = self.influxdb.timestamps(
            job_name, scenario_instance_id, agent_name,
            job_instance_id, suffix, condition,
        ) | self.elasticsearch.timestamps(
            job_name, scenario_instance_id, agent_name, job_instance_id,
        )

        if not timestamps:
            return None

        if only_bounds:
            return min(timestamps), max(timestamps)
        return sorted(timestamps)

    def suffixes(
            self, job_name=None, scenario_instance_id=None,
            agent_name=None, job_instance_id=None):
        """List the available suffixes in InfluxDB"""
        return self.influxdb.suffixes(job_name, scenario_instance_id, agent_name, job_instance_id)

    def scenarios(
            self, job_name=None, scenario_instance_id=None,
            agent_name=None, job_instance_id=None, suffix=None,
            fields=None, condition=None, timestamps=None):
        """Fetch data from InfluxDB and ElasticSearch that correspond to
        the given constraints and generate according `Scenario`s instances.
        """
        response = self.elasticsearch.logs(
                job_name, scenario_instance_id,
                agent_name, job_instance_id, timestamps)
        # Flatten scenarios instances from ElasticSearch
        scenarios = {
                (subscenario.instance_id,): subscenario
                for scenario in response
                for subscenario in scenario.scenarios
        }

        response = self.influxdb.statistics(
                job_name, scenario_instance_id, agent_name,
                job_instance_id, suffix, fields, condition, timestamps)
        # For each job found in InfluxDB
        for scenario_with_stats in response:
            for scenario_id, owner_id, job in extract_jobs(scenario_with_stats):
                # Retrieve the (existing) scenario holding it
                scenario = get_or_create_scenario(scenario_id, scenarios)
                owner = get_or_create_scenario(owner_id, scenarios)
                if owner is not scenario:
                    scenario.owner = owner
                    owner.sub_scenarios[(scenario.instance_id,)] = scenario
                # And set the statistics in the (existing) job instance
                existing_job = scenario.get_or_create_job(
                        job.name, job.instance_id, job.agent)
                existing_job.statistics_data = job.statistics_data

        # Filter top-level scenarios
        if scenario_instance_id is None:
            yield from (scenario for scenario in scenarios.values() if scenario.owner is None)
        else:
            with suppress(KeyError):
                yield scenarios[(scenario_instance_id,)]

    def import_scenario(self, scenario_instance):
        """Import the results of the `Scenario` instance in
        InfluxDB and ElasticSearch"""
        for scenario_id, owner_id, job in extract_jobs(scenario_instance):
            self.influxdb.import_job(scenario_id, owner_id, job)
            self.elasticsearch.import_job(scenario_id, owner_id, job)

    def remove_statistics(
            self, job_name=None, scenario_instance_id=None,
            agent_name=None, job_instance_id=None,
            suffix=None, condition=None, timestamps=None):
        """Delete data in InfluxDB that matches the given constraints"""
        self.influxdb.remove_statistics(
                job_name, scenario_instance_id, agent_name,
                job_instance_id, suffix, condition, timestamps)
        self.elasticsearch.remove_logs(
                job_name, scenario_instance_id, agent_name,
                job_instance_id, timestamps)

    def orphans(self, timestamps=None, condition=None):
        """Retrieve orphans logs from ElasticSearch and orphans
        statistics from InfluxDB.

        Orphans have no associated metadata such as scenario instance
        IDs or job instance IDs and are most likely not emitted using
        the collect-agent API.

        Returns a couple of a `Log` instance and a `Scenario` instance
        holding statistics data for each job (measurement) in InfluxDB.
        """
        logs = self.elasticsearch.orphans(timestamps)
        return logs, self.influxdb.orphans(condition, timestamps)
