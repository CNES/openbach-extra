#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2023 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

"""Collection of tools to fetch information from an InfluxDB server.

This module provide:
    * `ElasticSearchConnection`: a class to fetch and send data
    to/from an ElasticSearch server.
    * generic tools to format data when sending them to ElasticSearch.
"""

__author__ = 'Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>'
__credits__ = 'Maintainer: Mathias ETTINGER <mettinger@toulouse.viveris.com>'
__all__ = ['ElasticSearchConnection']


import json
import locale
import datetime
from contextlib import suppress

import requests

from .result_data import Log, get_or_create_scenario


############################################
# Helper functions for formatting purposes #
############################################

class LocaleManager():
    def __init__(self, loc):
        self.lc_all = locale.setlocale(locale.LC_ALL)
        self.locale = loc
          
    def __enter__(self):
        locale.setlocale(locale.LC_ALL, self.locale)
        return self
      
    def __exit__(self, exc_type, exc_value, exc_traceback):
        locale.setlocale(locale.LC_ALL, self.lc_all)
        

def tags_to_query(scenario, job, agent, job_instance, timestamps):
    """Build an ElasticSearch query out of the given parameters"""
    filter_query = {}

    if timestamps is not None:
        try:
            timestamp_lower, timestamp_upper = timestamps
        except (TypeError, ValueError):
            timestamp_lower = timestamp_upper = timestamps
        filter_query['filter'] = [{
            'range': {
                '@timestamp': {
                    'gte': timestamp_lower,
                    'lte': timestamp_upper,
                },
            },
        }]

    fields = {
        'scenario_instance_id:{0} || owner_scenario_instance_id:{0}': scenario,
        'program:{}': job,
        'agent_name:{}': agent,
        'job_instance_id:{}': job_instance,
    }
    query = ' && '.join(
            pattern.format(value)
            for pattern, value in fields.items()
            if value is not None)
    if query:
        filter_query['must'] = [{'query_string': {'query': query}}]
    else:
        filter_query['must'] = [{'match_all': {}}]

    return {'query': {'bool': filter_query}}


def extract_field_or_None(record, field_name, converter=str):
    """Helper function to easily convert a result from
    ElasticSearch into a meaningful data.
    """
    with suppress(LookupError, ValueError):
        return converter(record['fields'][field_name][0])


def extract_timestamp_or_None(record, field_name):
    """Helper function to easily convert a timestamp from
    ElasticSearch into a meaningful data.
    """
    with suppress(LookupError, ValueError):
        index = record['_index']
        timestamp = record['fields'][field_name][0]
        return parse_timestamp_with_index(timestamp, index)


def parse_timestamp_with_index(date, index, number_of_year_digits=4):
    """Convert a date representation from ElasticSearch into
    a timestamp as used throughout OpenBACH.
    """
    with LocaleManager('en_US.utf8'):
        year = int(index.split('.')[0][-number_of_year_digits:])
        timestamp = datetime.datetime.strptime(date, '%b %d %H:%M:%S')
        return int(timestamp.replace(year).timestamp() * 1000)


def parse_logs(elasticsearch_result):
    """Generate `Scenario`s instances from ElasticSearch stored data"""
    scenarios = {}  # Cache
    for record in elasticsearch_result:
        with suppress(KeyError):
            source = record['_source']
            agent = source['agent_name']
            job = source['program']
            job_id = source['job_instance_id']
            scenario = source['scenario_instance_id']
            owner = source['owner_scenario_instance_id']
            scenario = get_or_create_scenario(scenario, scenarios)
            owner = get_or_create_scenario(owner, scenarios)
            if owner is not scenario:
                scenario.owner = owner
            job = scenario.get_or_create_job(job, job_id, agent)

            _id = record['_id']
            index = record['_index']
            kind = record['_type']
            timestamp = parse_timestamp_with_index(source['timestamp'], index)
            version = source['@version']
            facility = source['facility']
            facility_label = source['facility_label']
            host = source['host']
            logsource = source['logsource']
            message = source['message']
            pid = source['pid']
            priority = source['priority']
            severity = source['severity']
            severity_label = source['severity_label']
            job.logs_data.add_log(
                    _id, kind, index, timestamp, version, facility,
                    facility_label, host, message, pid, priority,
                    severity, severity_label, logsource)

    # Filter top-level scenarios
    yield from (scenario for scenario in scenarios.values() if scenario.owner is None)


def parse_orphans(elasticsearch_result, log):
    """Populate a `Log` instance from ElasticSearch stored data
    where no scenario is associated to them.
    """
    for record in elasticsearch_result:
        source = record['_source']
        try:
            source['agent_name']
            source['program']
            source['job_instance_id']
            source['scenario_instance_id']
            source['owner_scenario_instance_id']
        except KeyError:
            with suppress(KeyError):
                _id = record['_id']
                index = record['_index']
                kind = record['_type']
                timestamp = parse_timestamp_with_index(source['timestamp'], index)
                version = source['@version']
                facility = source['facility']
                facility_label = source['facility_label']
                host = source['host']
                logsource = source['logsource']
                message = source['message']
                pid = source['pid']
                priority = source['priority']
                severity = source['severity']
                severity_label = source['severity_label']
                log.add_log(
                    _id, kind, index, timestamp, version, facility,
                    facility_label, host, message, pid, priority,
                    severity, severity_label, logsource)


def rest_protocol(job_name, scenario_id, owner_id, agent_name, job_id, logs):
    for _id, log in logs.items():
        timestamp = datetime.datetime.fromtimestamp(log._timestamp / 1000)
        metadata = {'index': {
            '_id': _id,
            '_index': log._index,
            '_type': log._type,
            '_routing': None,
        }}
        data = {
            'facility': log.facility,
            'facility_label': log.facility_label,
            'host': log.host,
            'job_instance_id': job_id,
            'scenario_instance_id': scenario_id,
            'owner_scenario_instance_id': owner_id,
            'agent_name': agent_name,
            'logsource': log.logsource if log.logsource else agent_name,
            'program': job_name,
            'message': log.message,
            'pid': log.pid,
            'priority': log.priority,
            'severity': log.severity,
            'severity_label': log.severity_label,
            'timestamp': timestamp.strftime('%b %d %H:%M:%S'),
            '@timestamp': timestamp.isoformat(timespec='milliseconds') + 'Z',
            '@version': log._version,
        }
        yield '{}\n{}\n'.format(json.dumps(metadata), json.dumps(data))


###############################
# Fetching and receiving data #
###############################

class ElasticSearchCommunicator:
    """Manage network access to an ElasticSearch server"""

    TIMEOUT = (2, 3600)  # Requests (connection, data) timeouts in second

    def __init__(self, ip, port=9200, credentials=None):
        """Configure the routes to send/get data to/from ElasticSearch"""

        base_url = 'http://{}:{}'.format(ip, port)
        self.settings_URL = base_url + '/logstash-*/_settings/'
        self.querying_URL = base_url + '/logstash-*/_search'
        self.writing_URL = base_url + '/_bulk'
        self.scrolling_URL = base_url + '/_search/scroll'
        self.deleting_URL = base_url + '/logstash-*/_delete_by_query'
        if credentials is None:
            self.auth_header = None
        else:
            self.auth_header = {'Authorization': 'Basic {}'.format(credentials)}

    def settings_query(self, *settings):
        filters = ','.join(settings)
        response = requests.get(self.settings_URL + filters, headers=self.auth_header, timeout=self.TIMEOUT)
        return response.json()

    def search_query(self, body=None, **query):
        """Send a query to ElasticSearch and gather the results"""

        query['scroll'] = '1m'
        session = requests.Session()
        response = session.post(self.querying_URL, params=query, json=body, headers=self.auth_header, timeout=self.TIMEOUT).json()
        while True:
            hits = response.get('hits', {}).get('hits', [])
            if not hits:
                break
            yield from hits
            try:
                scroll_id = response['_scroll_id']
            except KeyError:
                break
            body = {'scroll': '1m', 'scroll_id': scroll_id}
            response = session.post(self.scrolling_URL, json=body, headers=self.auth_header).json()

    def delete_query(self, query):
        """Send query to ElasticSearch so that matching logs are removed"""
        response = requests.post(self.deleting_URL, json=query, headers=self.auth_header, timeout=self.TIMEOUT)
        return response.json()

    def data_write(self, body, first_time_request=False):
        """Send data to ElasticSearch so they are stored"""
        if first_time_request:
            self.data_write(body)
        return requests.post(self.writing_URL, data=body.encode(), headers=self.auth_header, timeout=self.TIMEOUT)


class ElasticSearchConnection(ElasticSearchCommunicator):
    def agent_names(self, job=None, scenario=None, job_instance=None, timestamps=None):
        """List the available agent names in ElasticSearch
        that correspond to the given constraints.
        """
        field_name = 'agent_name'
        query = tags_to_query(scenario, job, None, job_instance, timestamps)
        response = self.search_query(query, fields=field_name)
        return {extract_field_or_None(record, field_name) for record in response}

    def job_names(self, scenario=None, agent=None, job_instance=None, timestamps=None):
        """List the available job names in ElasticSearch
        that correspond to the given constraints.
        """
        field_name = 'program'
        query = tags_to_query(scenario, None, agent, job_instance, timestamps)
        response = self.search_query(query, fields=field_name)
        return {extract_field_or_None(record, field_name) for record in response}

    def job_instance_ids(self, job=None, scenario=None, agent=None, timestamps=None):
        """List the available job instance IDs in ElasticSearch
        that correspond to the given constraints.
        """
        field_name = 'job_instance_id'
        query = tags_to_query(scenario, job, agent, None, timestamps)
        response = self.search_query(query, fields=field_name)
        return {extract_field_or_None(record, field_name, int) for record in response}

    def scenario_instance_ids(self, job=None, agent=None, job_instance=None, timestamps=None):
        """List the available scenario instance IDs in ElasticSearch
        that correspond to the given constraints.
        """
        field_name = 'scenario_instance_id'
        query = tags_to_query(None, job, agent, job_instance, timestamps)
        response = self.search_query(query, fields=field_name)
        return {extract_field_or_None(record, field_name, int) for record in response}

    def timestamps(self, job=None, scenario=None, agent=None, job_instance=None):
        """List the available timestamps in ElasticSearch
        that correspond to the given constraints.
        """
        field_name = 'timestamp'
        query = tags_to_query(scenario, job, agent, job_instance, None)
        response = self.search_query(query, fields=field_name)
        return {extract_timestamp_or_None(record, field_name) for record in response}

    def logs(self, job=None, scenario=None, agent=None, job_instance=None, timestamps=None):
        """Fetch data from ElasticSearch that correspond to the given
        constraints and generate according `Scenario`s instances.
        """
        query = tags_to_query(scenario, job, agent, job_instance, timestamps)
        response = self.search_query(query)
        yield from parse_logs(response)

    def all_logs(self, timestamps=None):
        """Fetch data from ElasticSearch that correspond to the given
        constraints and return the according logs.
        """
        query = tags_to_query(None, None, None, None, timestamps)
        response = self.search_query(query)
        return response

    def orphans(self, timestamps=None):
        """Fetch data from ElasticSearch that were not emitted using
        the collect-agent API and generate according `Log`s instances.
        """
        query = tags_to_query(None, None, None, None, timestamps)
        response = self.search_query(query)
        result = Log()
        parse_orphans(response, result)
        return result

    def remove_logs(self, job=None, scenario=None, agent=None, job_instance=None, timestamps=None):
        """Remove logs in ElasticSearch that
        correspond to the given constraints.
        """
        query = tags_to_query(scenario, job, agent, job_instance, timestamps)
        self.delete_query(query)

    def import_job(self, scenario_id, owner_id, job):
        """Write the data of the given job into ElasticSearch"""
        job_name = job.name
        agent_name = job.agent
        job_id = job.instance_id
        data_stream = rest_protocol(
                job_name, scenario_id, owner_id,
                agent_name, job_id, job.logs_data.numbered_data)
        for index, chunck in enumerate(data_stream):
            self.data_write(chunck, first_time_request=not index)
