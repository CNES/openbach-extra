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
   
   
   
   @file     frontend.py
   @brief    The frontend script (aggregate all the function callable by the user)
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import requests
import datetime
import pprint
from time import sleep
from urllib.parse import urlencode
from functools import partial, wraps
from sys import exit
import yaml
try:
    import simplejson as json
except ImportError:
    import json

config_file = 'config.yml'
with open(config_file, 'r') as stream:
    content = yaml.load(stream)
controller_ip = content['controller_ip']
if controller_ip is None:
    print('Please, fill the controller_ip in the config file')
    exit(1)

_URL = "http://" + controller_ip + ":8000/{}/"


def wait_for_success(state_function, status=None, valid_statuses=(200, 204),
                     **kwargs):
    while True:
        sleep(1)
        response = state_function(**kwargs).json()
        if status:
            response = response[status]
        returncode = response['returncode']
        if returncode != 202:
            print('Returncode:', returncode)
            pprint.pprint(response['response'])
            exit(returncode not in valid_statuses)


def _request_message(entry_point, verb, **kwargs):
    """Helper function to format a request and send it to
    the right URL.
    """

    url = _URL.format(entry_point)
    verb = verb.upper()

    if verb == 'GET':
        return requests.get(url, params=kwargs)
    else:
        body = json.dumps(kwargs)
        return requests.request(verb, url, data=body)


def pretty_print(function):
    """    
    warning terminate the program on error form the server
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        response = function(*args, **kwargs)
        print(response)
        if response.status_code != 204:
            pprint.pprint(response.json())
        if 400 <= response.status_code < 600:
            exit(1)
    return wrapper


def date_to_timestamp(date, fmt='%Y-%m-%d %H:%M:%S.%f'):
    timestamp = datetime.datetime.strptime(date, fmt).timestamp()
    return int(timestamp * 1000)


def add_collector(collector_ip, username, password, name, logs_port=None,
                  stats_port=None):
    action = _request_message
    if logs_port is not None:
        action = partial(action, logs_port=logs_port)
    if stats_port is not None:
        action = partial(action, stats_port=stats_port)
    return action('collector', 'POST', username=username, password=password,
                  address=collector_ip, name=name)


def modify_collector(collector_ip, logs_port=None, stats_port=None):
    action = _request_message
    if logs_port is not None:
        action = partial(action, logs_port=logs_port)
    if stats_port is not None:
        action = partial(action, stats_port=stats_port)
    return action('collector/{}'.format(collector_ip), 'PUT')


def del_collector(collector_ip):
    return _request_message('collector/{}'.format(collector_ip), 'DELETE')


def get_collector(collector_ip):
    return _request_message('collector/{}'.format(collector_ip), 'GET')


def list_collectors():
    return _request_message('collector', 'GET')


def install_agent(agent_ip, collector_ip, username, password, name):
    return _request_message('agent', 'POST', address=agent_ip,
                            username=username, password=password,
                            collector_ip=collector_ip, name=name)


def add_job(job_name, path):
    return _request_message('job', 'POST', name=job_name, path=path)


def uninstall_agent(agent_ip):
    return _request_message('agent/{}'.format(agent_ip), 'DELETE')


def del_job(job_name):
    return _request_message('job/{}'.format(job_name), 'DELETE')


def get_job_stats(job_name):
    return _request_message('job/{}'.format(job_name), 'GET', type='stats')


def get_job_help(job_name):
    return _request_message('job/{}'.format(job_name), 'GET', type='help')


def install_jobs(job_names, agent_ips):
    return _request_message(
            'job', 'POST', action='install',
            names=job_names, addresses=agent_ips)


def install_job(job_name, agent_ips):
    return _request_message('job/{}'.format(job_name), 'POST', action='install',
                            addresses=agent_ips)


def list_agents(update=None):
    action = _request_message
    if update:
        action = partial(action, update='')
    return action('agent', 'GET')


def list_jobs(string_to_search=None, ratio=None):
    if string_to_search:
        print ("ratio:", ratio)
        return _request_message('job', 'GET', string_to_search=string_to_search,
                               ratio=ratio)
    else:
        return _request_message('job', 'GET')
   
def list_installed_jobs(agent_ip, update=None):
    action = _request_message
    if update:
        action = partial(action, update='')
    return action('job', 'GET', address=agent_ip)


def list_job_instances(agent_ips, update=None):
    query_string = [('address', ip) for ip in agent_ips]
    if update:
        query_string.append(('update', ''))
    return requests.get(_URL.format('job_instance'),
                        params=urlencode(query_string))


def status_job_instance(job_instance_id, update=None):
    action = _request_message
    if update:
        action = partial(action, update='')
    return action('job_instance/{}'.format(job_instance_id), 'GET')


def push_file(local_path, remote_path, agent_ip):
    with open(local_path) as file_to_send:
        return requests.post(
                _URL.format('file'),
                data={'path': remote_path, 'agent_ip': agent_ip},
                files={'file': file_to_send})


def restart_job_instance(job_instance_id, arguments=None, date=None,
                         interval=None):
    action = _request_message
    if interval is not None:
        action = partial(action, interval=interval)
    if date is not None:
        action = partial(action, date=date)

    return action(
            'job_instance/{}'.format(job_instance_id),
            'POST', action='restart',
            instance_args={} if arguments is None else arguments)


def start_job_instance(agent_ip, job_name, arguments=None, date=None,
                       interval=None):
    action = _request_message
    if interval is not None:
        action = partial(action, interval=interval)
    if date is not None:
        action = partial(action, date=date)

    return action(
            'job_instance', 'POST', action='start',
            agent_ip=agent_ip, job_name=job_name,
            instance_args={} if arguments is None else arguments)


def retrieve_status_agents(agent_ips, update=False):
    action = _request_message
    if update:
        action = partial(action, update='')
    return action('agent', 'POST', action='retrieve_status',
                  addresses=agent_ips)


def assign_collector(address, collector_ip):
    return _request_message('agent/{}'.format(address), 'POST',
                            collector_ip=collector_ip)


def watch_job_instance(job_instance_id, date=None, interval=None, stop=None):
    action = _request_message
    if interval is not None:
        action = partial(action, interval=interval)
    if date is not None:
        action = partial(action, date=date)
    if stop is not None:
        action = partial(action, stop=stop)

    return action('job_instance/{}'.format(job_instance_id), 'POST',
                  action='watch')


def retrieve_status_jobs(agent_ips):
    return _request_message('job', 'POST', action='retrieve_status',
                            addresses=agent_ips)


def stop_job_instance(job_instance_ids, date=None):
    action = _request_message
    if date is not None:
        action = partial(action, date=date)

    return action('job_instance', 'POST', action='stop',
                  job_instance_ids=job_instance_ids)


def uninstall_jobs(job_names, agent_ips):
    return _request_message(
            'job', 'POST', action='uninstall',
            names=job_names, addresses=agent_ips)


def uninstall_job(job_name, agent_ips):
    return _request_message('job/{}'.format(job_name), 'POST',
                            action='uninstall', addresses=agent_ips)


def set_job_log_severity(
        agent_ip, job_name, severity,
        local_severity=None, date=None):
    action = _request_message
    if local_severity is not None:
        action = partial(action, local_severity=local_severity)
    if date is not None:
        action = partial(action, date=date)

    return action(
            'job/{}'.format(job_name), 'POST',
            action='log_severity', addresses=[agent_ip], severity=severity)


def set_job_stat_policy(
        agent_ip, job_name, stat_name='default',
        storage=None, broadcast=None, date=None):
    action = _request_message
    if storage is not None:
        action = partial(action, storage=storage)
    if broadcast is not None:
        action = partial(action, broadcast=broadcast)
    if date is not None:
        action = partial(action, date=date)

    return action(
            'job/{}'.format(job_name), 'POST',
            action='stat_policy',
            stat_name=stat_name, addresses=[agent_ip])


def create_scenario(scenario_json, project_name=None):
    if project_name is not None:
        return _request_message('project/{}/scenario'.format(project_name),
                                'POST', **scenario_json)
    else:
        return _request_message('scenario', 'POST', **scenario_json)


def del_scenario(scenario_name, project_name=None):
    if project_name is not None:
        return _request_message('project/{}/scenario/{}'.format(project_name,
                                                                scenario_name),
                                'DELETE')
    else:
        return _request_message('scenario/{}'.format(scenario_name), 'DELETE')


def modify_scenario(scenario_name, scenario_json, project_name=None):
    if project_name is not None:
        return _request_message('project/{}/scenario/{}'.format(project_name,
                                                                scenario_name),
                                'PUT', **scenario_json)
    else:
        return _request_message('scenario/{}'.format(scenario_name), 'PUT',
                                **scenario_json)


def get_scenario(scenario_name, project_name=None):
    if project_name is not None:
        return _request_message('project/{}/scenario/{}'.format(project_name,
                                                                scenario_name),
                                'GET')
    else:
        return _request_message('scenario/{}'.format(scenario_name), 'GET')


def list_scenarios(project_name=None):
    if project_name is not None:
        return _request_message('project/{}/scenario'.format(project_name),
                                'GET')
    else:
        return _request_message('scenario', 'GET')


def start_scenario_instance(name, args, date=None, project_name=None):
    action = _request_message
    if date is not None:
        action = partial(action, date=date)
    if project_name is None:
        return action('scenario_instance', 'POST', scenario_name=name,
                      args=args)
    else:
        return action('project/{}/scenario/{}/scenario_instance'.format(
            project_name, name), 'POST', args=args)


def stop_scenario_instance(scenario_instance_id, date=None, scenario_name=None,
                           project_name=None):
    action = _request_message
    if date is not None:
        action = partial(action, date=date)

    if project_name is not None and scenario_name is not None:
        return action('project/{}/scenario/{}/scenario_instance/{}'.format(
            project_name, scenario_name, scenario_instance_id), 'POST')
    else:
        return action('scenario_instance/{}'.format(scenario_instance_id),
                      'POST')


def list_scenario_instances(scenario_name=None, project_name=None):
    if project_name is not None:
        if scenario_name is not None:
            return _request_message('project/{}/scenario/{}/scenario_instance'.format(
                project_name, scenario_name), 'GET')
        else:
            return _request_message('project/{}/scenario_instance'.format(
                project_name), 'GET')
    else:
        return _request_message('scenario_instance', 'GET')


def status_scenario_instance(scenario_instance_id, scenario_name=None,
                             project_name=None):
    if project_name is not None and scenario_name is not None:
        return _request_message('project/{}/scenario/{}/scenario_instance/{}'.format(
            project_name, scenario_name, scenario_instance_id), 'GET')
    else:
        return _request_message('scenario_instance/{}'.format(
            scenario_instance_id), 'GET')


def kill_all(date=None):
    action = _request_message
    if date is not None:
        action = partial(action, date=date)

    return action('job_instance', 'POST', action='kill')


def add_project(project_json):
    return _request_message('project', 'POST', **project_json)


def modify_project(project_name, project_json):
    return _request_message('project/{}'.format(project_name), 'PUT',
                            **project_json)


def del_project(project_name):
    return _request_message('project/{}'.format(project_name), 'DELETE')


def get_project(project_name):
    return _request_message('project/{}'.format(project_name), 'GET')


def list_projects():
    return _request_message('project', 'GET')


def state_collector(address):
    return _request_message('collector/{}/state'.format(address), 'GET')


def state_agent(address):
    return _request_message('agent/{}/state'.format(address), 'GET')


def state_job(address, name):
    return _request_message('job/{}/state'.format(name), 'GET',
                            address=address,)


def state_push_file(filename, path, agent_ip):
    return _request_message('file/state', 'GET', filename=filename, path=path,
                            agent_ip=agent_ip)


def state_job_instance(job_instance_id):
    return _request_message('job_instance/{}/state'.format(job_instance_id))

