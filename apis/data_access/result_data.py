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

"""Collection of classes allowing a meaningful representation of data
stored on a collector.
"""

__author__ = 'Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>'
__credits__ = 'Maintainer: Mathias ETTINGER <mettinger@toulouse.viveris.com>'


import json
from collections import OrderedDict


class Scenario:
    """Container of data for a whole scenario instance.

    Hold informations about jobs and sub-scenario instances and
    can generate informations about agents too.
    """

    def __init__(self, instance_id, owner=None):
        self.instance_id = instance_id
        self.owner = owner
        self.job_instances = {}
        self.sub_scenarios = {}

    def __eq__(self, other):
        if not isinstance(other, Scenario):
            raise NotImplementedError

        return (
                self.instance_id == other.instance_id and
                self.owner == other.owner and
                self.job_instances == other.job_instances and
                self.sub_scenarios == other.sub_scenarios
        )

    def get_or_create_subscenario(self, instance_id):
        return _get_or_create(self.sub_scenarios, Scenario, instance_id)

    def get_or_create_job(self, name, instance_id, agent):
        return _get_or_create(self.job_instances, Job, name, instance_id, agent)

    @property
    def owner_instance_id(self):
        if self.owner is None:
            return self.instance_id
        return self.owner.instance_id

    @property
    def own_jobs(self):
        """Generator of `Job` instances associated to this scenario"""
        yield from self.job_instances.values()

    @property
    def jobs(self):
        """Generator of `Job` instances associated to this
        scenario and all its subscenarios, recursively.
        """
        for scenario in self.scenarios:
            yield from scenario.own_jobs

    @property
    def own_scenarios(self):
        """Generator of sub-`Scenario` instances associated to this scenario"""
        yield from self.sub_scenarios.values()

    @property
    def scenarios(self):
        """Generator of sub-`Scenario` instances associated to this
        scenario and all its subscenarios, recursively.

        Guaranteed to generate at least this scenario as first element.
        """
        yield self
        for scenario in self.own_scenarios:
            yield from scenario.scenarios

    @property
    def own_agents(self):
        """Generator of `Agent` instances associated to this scenario"""
        agents = {}
        for job in self.own_jobs:
            agent = _get_or_create(
                    agents, Agent,
                    job.agent, self.instance_id,
                    args=(job.agent, self))
            agent.job_instances[(job.name, job.instance_id)] = job
        yield from agents.values()

    @property
    def agents(self):
        """Generator of `Agent` instances associated to this
        scenario and all its subscenarios, recursively.
        """
        agents = {}
        for scenario in self.scenarios:
            for job in scenario.own_jobs:
                agent = _get_or_create(
                        agents, Agent,
                        job.agent, scenario.instance_id,
                        args=(job.agent, scenario))
                agent.jobs[(job.name, job.instance_id)] = job
        yield from agents.values()

    @property
    def json(self):
        """Build a JSON representation of this Scenario instance"""
        return {
            'scenario_instance_id': self.instance_id,
            'owner_scenario_instance_id': self.owner_instance_id,
            'sub_scenario_instances': [scenario.json for scenario in self.own_scenarios],
            'agents': [agent.json for agent in self.own_agents],
            'jobs': [job.json for job in self.own_jobs],
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
        try:
            jobs = scenario_data['jobs']
        except KeyError:
            # Maybe an old file format
            for agent_data in scenario_data['agents']:
                agent_name = agent_data['name']
                for job_data in agent_data['job_instances']:
                    job_data['agent_name'] = agent_name
                    job = Job.load(job_data)
                    key = (job.name, job.instance_id, job.agent)
                    scenario_instance.job_instances[key] = job
        else:
            for job_data in jobs:
                job = Job.load(job_data)
                key = (job.name, job.instance_id, job.agent)
                scenario_instance.job_instances[key] = job
        return scenario_instance


class Agent:
    """Container of data for job instances launched on a single
    machine. An agent is tied to a `Scenario` instance at
    construction time.

    Any job added to this `Agent` will be added to the associated
    `Scenario` too.
    """

    def __init__(self, name, scenario):
        self._scenario = scenario
        self.name = name
        self.job_instances = OrderedDict({})

    def get_or_create_job(self, name, instance_id):
        return _get_or_create(
                self.job_instances,
                self._scenario.get_or_create_job,
                name, instance_id,
                args=(name, instance_id, self.name))

    @property
    def json(self):
        """Build a JSON representation of this Agent instance"""
        return {
            'agent_name': self.name,
            'scenario_instance_id': self._scenario.instance_id,
            'jobs': [job.json for job in self.job_instances.values()],
        }


class _StatisticsProxy:
    def __init__(self, statistics_data):
        self.__data = statistics_data

    def __call__(self, suffix=None):
        try:
            return self.__data[(suffix,)]
        except KeyError:
            raise AttributeError('\'Job\' object has no statistics attribute for the suffix {}'.format(suffix)) from None

    def __getattr__(self, name):
        if name.startswith(self.__class__.__name__ + '__'):
            return super().__getattr__(name)
        return getattr(self(), name)

    def __setattr__(self, name, value):
        if name.startswith(self.__class__.__name__ + '__'):
            return super().__setattr__(name, value)
        return setattr(self(), name, value)

    def __delattr__(self, name):
        if name.startswith(self.__class__.__name__ + '__'):
            return super().__delattr__(name)
        return delattr(self(), name, value)


class Job:
    """Container of data for job instances.

    Hold informations about statistics associated to suffixes.
    """

    def __init__(self, name, instance_id, agent):
        self.name = name
        self.instance_id = instance_id
        self.agent = agent
        self.statistics_data = {}
        self.logs_data = Log()

    def __eq__(self, other):
        if not isinstance(other, Job):
            raise NotImplementedError

        return (
                self.name == other.name and
                self.instance_id == other.instance_id and
                self.agent == other.agent and
                self.statistics_data == other.statistics_data and
                self.logs_data == other.logs_data
        )

    def get_or_create_statistics(self, suffix=None):
        return _get_or_create(self.statistics_data, Statistic, suffix, args=())

    @property
    def statistics(self):
        """Wraps data into a proxy to ease exploration"""
        return _StatisticsProxy(self.statistics_data)

    @property
    def suffixes(self):
        yield from (suffix for suffix, in self.statistics_data)

    @property
    def stats(self):
        """Build a JSON representation of statistics hold by
        this Job instance.
        """
        return [{
            'suffix': suffix,
            'data': statistics.json,
        } for (suffix,), statistics in self.statistics_data.items()]

    @property
    def logs(self):
        """Build a JSON representation of logs hold by
        this Job instance.
        """
        return self.logs_data.json

    @property
    def json(self):
        """Build a JSON representation of this Job instance"""
        return {
            'job_instance_id': self.instance_id,
            'job_name': self.name,
            'agent_name': self.agent,
            'logs': self.logs,
            'statistics': self.stats,
        }

    @classmethod
    def load(cls, job_data):
        """Generate a Job instance from a JSON representation"""
        name = job_data['job_name']
        agent = job_data['agent_name']
        instance_id = job_data['job_instance_id']
        job_instance = cls(name, instance_id, agent)
        job_instance.logs_data = Log.load(job_data['logs'])
        try:
            statistics = job_data['statistics']
        except KeyError:
            # Maybe an old file format
            for suffix_data in job_data['suffixes']:
                suffix = suffix_data['name']
                stats_data = suffix_data['statistics']
                stats = Statistic.load(stats_data)
                job_instance.statistics_data[(suffix,)] = stats
        else:
            for statistic in statistics:
                suffix = statistic['suffix']
                stats_data = statistic['data']
                stats = Statistic.load(stats_data)
                job_instance.statistics_data[(suffix,)] = stats
        return job_instance


class Statistic:
    def __init__(self):
        self.dated_data = OrderedDict({})

    def __eq__(self, other):
        if not isinstance(other, Statistic):
            raise NotImplementedError

        return self.dated_data == other.dated_data

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
            try:
                timestamp = stats['time']
            except KeyError:
                # Maybe an old file format
                timestamp = stats['timestamp']
            stats_data = {k: v for k, v in stats.items() if k != 'time'}
            stats_data['timestamp'] = timestamp
            statistic_instance.add_statistic(**stats_data)
        return statistic_instance


class _LogEntry:
    def __init__(self, _id, _type, _index, _timestamp, _version,
                 facility, facility_label, host, message, pid,
                 priority, severity, severity_label, source):
        self._id = _id
        self._index = _index
        self._type = _type
        self._timestamp = _timestamp
        self._version = _version
        self.facility = facility
        self.facility_label = facility_label
        self.host = host
        self.logsource = source
        self.message = message
        self.pid = pid
        self.priority = priority
        self.severity = severity
        self.severity_label = severity_label

    def __eq__(self, other):
        if not isinstance(other, _LogEntry):
            return NotImplementedError

        return (
                self._id == other._id and
                self._index == other._index and
                self._type == other._type and
                self._timestamp == other._timestamp and
                self._version == other._version and
                self.facility == other.facility and
                self.facility_label == other.facility_label and
                self.host == other.host and
                self.logsource == other.logsource and
                self.message == other.message and
                self.pid == other.pid and
                self.priority == other.priority and
                self.severity == other.severity and
                self.severity_label == other.severity_label
        )

    @property
    def json(self):
        return {
                '_id': self._id, '_index': self._index, '_type': self._type,
                '_timestamp': self._timestamp, '_version': self._version,
                'facility': self.facility, 'severity': self.severity,
                'facility_label': self.facility_label, 'pid': self.pid,
                'message': self.message, 'priority': self.priority,
                'host': self.host, 'severity_label': self.severity_label,
                'source': self.logsource,
        }


class Log:
    def __init__(self):
        self.numbered_data = {}

    def __eq__(self, other):
        if not isinstance(other, Log):
            raise NotImplementedError

        return self.numbered_data == other.numbered_data

    def add_log(self, _id, _type, _index, _timestamp, _version,
                facility, facility_label, host, message, pid,
                priority, severity, severity_label, source):
        self.numbered_data[_id] = _LogEntry(
                _id, _type, _index, _timestamp, _version,
                facility, facility_label, host, message, pid,
                priority, severity, severity_label, source)

    @property
    def json(self):
        """Build a JSON representation of this Log instance"""
        return [log.json for log in self.numbered_data.values()]

    @classmethod
    def load(cls, logs_data):
        """Generate a Log instance from a JSON representation"""
        log_instance = cls()
        for log in logs_data:
            if 'type' in log:
                # Maybe an old file format
                log = log.copy()
                log['source'] = ''
                log['_type'] = log.pop('type')
                del log['flag']
            log_instance.add_log(**log)
        return log_instance


def _get_or_create(container, constructor, *key, args=None):
    """Custom implementation of a `setdefault`-like
    accessor on dictionaries; but allow for costy
    object creation on KeyError rather than upfront.

    Return the value associated to the given key in
    the given container. If the key is no present,
    create an instance of the required object, store
    it in the container and return it.
    """
    try:
        return container[key]
    except KeyError:
        if args is None:
            args = key
        container[key] = instance = constructor(*args)
        return instance


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
    """Retrieve a `Scenario` instance from the cache or
    create a new one if it doesn't already exists.
    """
    return _get_or_create(cache, Scenario, scenario_id)


def extract_jobs(scenario):
    """Extract out `Job`s from a `Scenario` instance indexed by
    their sub-scenario instance.
    """
    for subscenario in scenario.scenarios:
        for job in subscenario.own_jobs:
            yield subscenario.instance_id, subscenario.owner_instance_id, job
