#!/usr/bin/env python3

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

"""Collection of classes allowing a meaningful representation of data
stored on a collector.
"""

__author__ = 'Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>'
__credits__ = 'Maintainer: Mathias ETTINGER <mettinger@toulouse.viveris.com>'


import json
from collections import OrderedDict


class Scenario:
    def __init__(self, instance_id, owner=None):
        self.instance_id = instance_id
        self.owner = owner
        self.job_instances = OrderedDict({})
        self.sub_scenarios = OrderedDict({})

    def get_or_create_subscenario(self, instance_id):
        try:
            scenario = self.sub_scenarios[instance_id]
        except KeyError:
            self.sub_scenarios[instance_id] = scenario = Scenario(instance_id, self)
            if self.owner is not None:
                self.owner._new_scenario(instance_id, scenario)
        return scenario

    def _new_scenario(self, instance_id, scenario):
        self.sub_scenarios[instance_id] = scenario
        if self.owner is not None:
            self.owner._new_scenario(instance_id, scenario)

    def get_or_create_job(self, name, instance_id, agent):
        key = (name, instance_id, agent)
        try:
            job = self.job_instances[key]
        except KeyError:
            self.job_instances[key] = job = Job(*key)
            if self.owner is not None:
                self.owner._new_job(key, job)
        return job

    def _new_job(self, key, job):
        self.job_instances[key] = job
        if self.owner is not None:
            self.owner._new_job(key, job)

    @property
    def owner_instance_id(self):
        if self.owner is None:
            return self.instance_id
        return self.owner.instance_id

    @property
    def jobs(self):
        yield from self.job_instances.values()

    @property
    def agents(self):
        sub_jobs = set(scenario.jobs for scenario in self.scenarios)

        agents = {}
        for job in self.jobs:
            if job in sub_jobs:
                continue
            key = (job.agent, self.instance_id)
            try:
                agent = agents[key]
            except KeyError:
                agents[key] = agent = Agent(job.agent, self)
            agent.jobs[(job.name, job.instance_id)] = job

        yield from agents.values()
        for scenario in self.scenarios:
            yield from scenario.agents

    @property
    def scenarios(self):
        yield from self.sub_scenarios.values()

    @property
    def recursive_scenarios(self):
        yield self
        for scenario in self.sub_scenarios.values():
            yield from scenario.recursive_scenarios

    @property
    def json(self):
        """Build a JSON representation of this Scenario instance"""
        return {
            'scenario_instance_id': self.instance_id,
            'owner_scenario_instance_id': self.owner_instance_id,
            'sub_scenario_instances': [scenario.json for scenario in self.scenarios],
            'agents': [agent.json for agent in self.agents],
            'jobs': [job.json for job in self.jobs],
        }

    @classmethod
    def load(cls, scenario_data):
        """Generate a Scenario instance from a JSON representation"""
        instance_id = scenario_data['scenario_instance_id']
        # owner_id = scenario_data['owner_scenario_instance_id']
        scenario_instance = cls(instance_id)
        for sub_scenario_data in scenario_data['sub_scenario_instances']:
            sub_scenario = cls.load(sub_scenario_data)
            sub_scenario.owner = scenario_instance
            scenario_instance.sub_scenarios[sub_scenario.instance_id] = sub_scenario
        for job_data in scenario_data['jobs']:
            job_instance = Job.load(job_data)
            key = (job_instance.name, job_instance.agent, job_instance.instance_id)
            scenario_instance.job_instances[key] = job_instance
        return scenario_instance


class Agent:
    def __init__(self, name, scenario):
        self._scenario = scenario
        self.name = name
        self.job_instances = OrderedDict({})

    def get_or_create_job(self, name, instance_id):
        key = (name, instance_id)
        try:
            job = self.job_instances[key]
        except KeyError:
            job = self._scenario.get_or_create_job(name, self.name, instance_id)
            self.job_instancess[key] = job
        return job

    @property
    def json(self):
        """Build a JSON representation of this Agent instance"""
        return {
            'agent_name': self.name,
            'scenario_instance_id': self._scenario.instance_id,
            'jobs': [job.json for job in self.jobs.values()],
        }


class Job:
    def __init__(self, name, instance_id, agent):
        self.name = name
        self.instance_id = instance_id
        self.agent = agent
        self.statistics_data = OrderedDict({})
        self.logs_data = Log()

    def get_or_create_statistics(self, suffix=None):
        try:
            statistics = self.statistics_data[suffix]
        except KeyError:
            self.statistics_data[suffix] = statistics = Statistic()
        return statistics

    @property
    def statistics(self):
        return [{
            'suffix': suffix,
            'data': statistics.json,
        } for suffix, statistics in self.statistics_data.items()]

    @property
    def logs(self):
        return self.logs_data.json

    @property
    def json(self):
        """Build a JSON representation of this Job instance"""
        return {
            'job_instance_id': self.instance_id,
            'job_name': self.name,
            'agent_name': self.agent,
            'logs': self.logs,
            'statistics': self.statistics,
        }

    @classmethod
    def load(cls, job_data):
        """Generate a Job instance from a JSON representation"""
        name = job_data['job_name']
        agent = job_data['agent_name']
        instance_id = job_data['job_instance_id']
        job_instance = cls(name, agent, instance_id)
        job_instance.logs_data = Log.load(job_data['logs'])
        for statistic in job_data['statistics']:
            suffix = statistic['suffix']
            stats_data = statistic['data']
            job_instance[suffix] = Statistic.load(stats_data)
        return job_instance


class Statistic:
    def __init__(self):
        self.dated_data = OrderedDict({})

    def add_statistic(self, timestamp, **kwargs):
        self.dated_data[timestamp] = kwargs

    @property
    def json(self):
        """Build a JSON representation of this Statistic instance"""
        return [
            {'time': timestamp, **stats}
            for timestamp, stats in self.dated_data.items()
        ]

    @classmethod
    def load(cls, statistics_data):
        """Generate a Statistic instance from a JSON representation"""
        statistic_instance = cls()
        for stats in statistics_data:
            statistic_instance.dated_data[stats['time']] = stats
        return statistic_instance


class Log:
    def __init__(self):
        self.numbered_data = OrderedDict({})

    def add_log(self, _id, _index, _timestamp, _version, facility,
                facility_label, flag, host, message, pid, priority,
                severity, severity_label, type):
        self.numbered_data[_id] = {
                '_id': _id,
                '_index': _index,
                '_timestamp': _timestamp,
                '_version': _version,
                'facility': facility,
                'facility_label': facility_label,
                'flag': flag,
                'host': host,
                'message': message,
                'pid': pid,
                'priority': priority,
                'severity': severity,
                'severity_label': severity_label,
                'type': type,
        }

    @property
    def json(self):
        """Build a JSON representation of this Log instance"""
        return [log for log in self.numbered_data.values()]

    @classmethod
    def load(cls, logs_data):
        """Generate a Log instance from a JSON representation"""
        log_instance = cls()
        for log in logs_data:
            log_instance[log['_id']] = log
        return log_instance


def read_scenario(filename):
    """Generate a `Scenario` instance from a file.

    The file should contain the equivalent of a JSON
    dump of the dictionary returned by the `json` property
    of the corresponding `Scenario` instance.
    """

    with open(filename) as f:
        scenario_json = json.load(f)
    return Scenario.load(scenario_json)


def get_or_create_scenario(scenario_id, cache):
    try:
        return cache[scenario_id]
    except KeyError:
        cache[scenario_id] = scenario = Scenario(scenario_id)
        return scenario


def extract_jobs(scenario, context=None):
    """Extract out `Job`s from a `Scenario` instance indexed by
    their sub-scenario instance.

    This function is recursive and uses the `context` parameter
    to keep track of already emitted jobs. You should not provide
    any value unless you want to filter out some jobs.
    """
    if context is None:
        # Cache of already yielded jobs
        context = set()

    # Yield jobs for sub-scenarios first to populate the cache
    for subscenario in scenario.scenarios:
        yield from extract_jobs(subscenario, context)

    # Yield each remaining job of the current scenario
    scenario_id = scenario.instance_id
    owner_id = scenario.owner_instance_id
    for job in scenario.jobs:
        if job not in context:
            context.add(job)  # Inform the caller we took care of it
            yield scenario_id, owner_id, job
