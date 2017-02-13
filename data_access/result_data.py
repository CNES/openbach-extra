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



   @file     result_data.py
   @brief    
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import functools
from collections import OrderedDict


def ForeignKey(cls, key):
    """ Metaclass """
    class Auto(type):
        def __call__(mcls, *args, **kwargs):
            """At construction, put our instance into the attributes of
            the other end of the relationship.
            """
            instance = super().__call__(*args, **kwargs)
            attrname = mcls.__name__.lower() + 's'
            for arg in args + tuple(kwargs.values()):
                if isinstance(arg, cls):
                    getattr(arg, attrname)[getattr(instance, key)] = instance
            return instance

        def __init__(mcls, name, bases, dct):
            """At creation, setup a dictionnary into the other end of
            the relationship to store our instances.
            """
            mcls_name = mcls.__name__.lower()
            super().__init__(name, bases, dct)
            attrname = mcls_name + 's'
            # Decorate the other end's __init__
            def initter(init):
                """Setup an empty dictionnary"""
                @functools.wraps(init)
                def wrapper(self, identificator, *args, **kwargs):
                    init(self, identificator, *args, **kwargs)
                    setattr(self, attrname, OrderedDict())
                return wrapper
            cls.__init__ = initter(cls.__init__)
            # Add an accessor for a given foreign key
            def getter(self, identificator, *args, **kwargs):
                """Cache foreign keys in a dictionnary"""
                try:
                    return getattr(self, attrname)[identificator]
                except KeyError:
                    return mcls(identificator, self, *args, **kwargs)
            methodname = 'get_' + mcls_name
            if not hasattr(cls, methodname):
                setattr(cls, methodname, getter)
            # Add an iterator over foreign keys
            def instances_getter(self):
                return iter(getattr(self, attrname).values())
            methodname = mcls_name + '_iter'
            if not hasattr(cls, methodname):
                setattr(cls, methodname, property(instances_getter))
    return Auto


class ScenarioInstanceResult:
    """ Structure that represents all the results of a Scenario Instance """
    def __init__(self, scenario_instance_id, owner_scenario_instance_id):
        self.scenario_instance_id = scenario_instance_id
        self.owner_scenario_instance_id = owner_scenario_instance_id
        self.sub_scenario_instances = {}

    @property
    def json(self):
        """Return a JSON representation of the Scenario"""
        info_json = {
            'scenario_instance_id': self.scenario_instance_id,
            'owner_scenario_instance_id': self.owner_scenario_instance_id,
            'sub_scenario_instances': [scenario_instance.json for
                                       scenario_instance in
                                       self.sub_scenario_instances.values()],
            'agents': [agent.json for agent in self.agentresult_iter]
        }
        return info_json

    @classmethod
    def load(cls, scenario_data):
        """Generate a ScenarioInstanceResult instance from a JSON representation"""
        instance_id = scenario_data['scenario_instance_id']
        owner_id = scenario_data['owner_scenario_instance_id']
        instance = cls(instance_id, owner_id)
        for agent_data in scenario_data['agents']:
            agent = AgentResult.load(agent_data, instance)
            instance.agentresults[agent.name] = agent
        for sub_scenario_data in scenario_data['sub_scenario_instances']:
            sub_scenario = cls.load(sub_scenario_data)
            sub_instance_id = sub_scenario.scenario_instance_id
            instance.sub_scenario_instances[sub_instance_id] = sub_scenario
        return instance


class AgentResult(metaclass=ForeignKey(ScenarioInstanceResult, 'name')):
    """ Structure that represents all the results of an Agent """
    def __init__(self, name, scenario_instance):
        self.name = name
        self.ip = None
        self.scenario_instance = scenario_instance

    @property
    def json(self):
        """Return a JSON representation of the Agent"""
        info_json = {
            'name': self.name,
            'job_instances': [job_instance.json for job_instance in
                              self.jobinstanceresult_iter]
        }
        if self.ip is not None:
            info_json['ip'] = self.ip
        return info_json

    @classmethod
    def load(cls, agent_data, scenario=None):
        """Generate a AgentResult instance from a JSON representation"""
        name = agent_data['name']
        ip = agent_data.get('ip')
        instance = cls(name, scenario_instance=scenario)
        instance.ip = ip
        for job_data in agent_data['job_instances']:
            job = JobInstanceResult.load(job_data, instance)
            instance.jobinstanceresults[job.job_instance_id] = job
        return instance


class JobInstanceResult(metaclass=ForeignKey(AgentResult, 'job_instance_id')):
    """ Structure that represents all the results of a Job Instance """
    def __init__(self, job_instance_id, agent, job_name):
        self.job_instance_id = job_instance_id
        self.job_name = job_name
        self.agent = agent

    def get_statisticresults(self, suffix_name):
        """ Function that returns the statistic results with the specific suffix
        """
        return self.suffixresults[suffix_name].statisticresults

    @property
    def statisticresults(self):
        """Return the StatisticResults with no suffix"""
        try:
            return self.suffixresults[None].statisticresults
        except KeyError:
            return {}

    @property
    def json(self):
        """Return a JSON representation of the Job"""
        return {
            'job_instance_id': self.job_instance_id,
            'job_name': self.job_name,
            'logs': [log.json for log in self.logresult_iter],
            'suffixes': [suffix.json for suffix in self.suffixresult_iter]
        }

    @classmethod
    def load(cls, job_data, agent=None):
        """Generate a JobInstanceResult instance from a JSON representation"""
        name = job_data['job_name']
        instance_id = job_data['job_instance_id']
        instance = cls(instance_id, agent=agent, job_name=name)
        for suffix_data in job_data['suffixes']:
            suffix = SuffixResult.load(suffix_data, instance)
            instance.suffixresults[suffix.name] = suffix
        for log_data in job_data['logs']:
            log = LogResult.load(log_data, instance)
            instance.logresults[log._id] = log
        return instance


class SuffixResult(metaclass=ForeignKey(JobInstanceResult, 'name')):
    """ Structure that represents all the results of a Suffix """
    def __init__(self, name, job_instance):
        self.name = name
        self.job_instance = job_instance

    @property
    def json(self):
        """Return a JSON representation of the Suffix"""
        info_json = {
            'name': self.name,
            'statistics': [stat.json for stat in self.statisticresult_iter]
        }
        return info_json

    @classmethod
    def load(cls, suffix_data, job=None):
        """Generate a SuffixResult instance from a JSON representation"""
        name = suffix_data['name']
        instance = cls(name, job_instance=job)
        for statistic_data in suffix_data['statistics']:
            statistic = StatisticResult.load(statistic_data, instance)
            instance.statisticresults[statistic.timestamp] = statistic
        return instance


class StatisticResult(metaclass=ForeignKey(SuffixResult, 'timestamp')):
    """ Structure that represents all the results of a Statistic """
    def __init__(self, timestamp, suffix, **kwargs):
        self.timestamp = timestamp
        self.suffix = suffix
        self.values = kwargs

    @property
    def json(self):
        """Return a JSON representation of the Statistic"""
        info_json = self.values.copy()
        info_json['timestamp'] = self.timestamp
        return info_json

    @classmethod
    def load(cls, statistic_data, suffix=None):
        """Generate a StatisticResult instance from a JSON representation"""
        return cls(suffix=suffix, **statistic_data)


class LogResult(metaclass=ForeignKey(JobInstanceResult, '_id')):
    """ Structure that represents a Log """
    def __init__(self, _id, job_instance, _index, _timestamp, _version,
                 facility, facility_label, flag, host, message, pid, priority,
                 severity, severity_label, type):
        self._id = _id
        self._index = _index
        self._timestamp = _timestamp
        self._version = _version
        self.facility = facility
        self.facility_label = facility_label
        self.flag = flag
        self.host = host
        self.message = message
        self.pid = pid
        self.priority = priority
        self.severity = severity
        self.severity_label = severity_label
        self.type = type
        self.job_instance = job_instance

    @property
    def json(self):
        """Return a JSON representation of the Log"""
        return {key: value for key, value in vars(self).items()
                if key != 'job_instance'}

    @classmethod
    def load(cls, log_data, job=None):
        """Generate a LogResult instance from a JSON representation"""
        return cls(job_instance=job, **log_data)
