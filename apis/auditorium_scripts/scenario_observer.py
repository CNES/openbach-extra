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


"""Framework for easier Scenario post-processing"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''

import re
import time
import json
import pprint
import logging
import datetime
from pathlib import Path
from sys import exit, stderr
from contextlib import suppress

import requests
from data_access import CollectorConnection
from data_access.elasticsearch_tools import ElasticSearchConnection

from auditorium_scripts.frontend import FrontendBase
from auditorium_scripts.create_scenario import CreateScenario
from auditorium_scripts.get_scenario import GetScenario
from auditorium_scripts.list_scenarios import ListScenarios
from auditorium_scripts.modify_scenario import ModifyScenario
from auditorium_scripts.start_scenario_instance import StartScenarioInstance
from auditorium_scripts.status_scenario_instance import StatusScenarioInstance
from auditorium_scripts.get_scenario_instance_data import GetScenarioInstanceData


MAX_RETRIES_STATUS = 5


class ScenarioObserver(FrontendBase):
    def __init__(self, **default_run_arguments):
        super().__init__('OpenBACH — Run a scenario and post-process stats')
        self._last_instance = {
                'scenario_instance_id': -1,
                'scenario_name': None,
                'openbach_functions': [],
        }
        self._default_arguments = default_run_arguments
        self.build_parser()

    def build_parser(self):
        self.scenario_group = self.parser.add_argument_group('scenario arguments')
        self.add_scenario_argument(
                'project_name', metavar='PROJECT_NAME',
                help='name of the project the scenario is associated with')
        self.add_scenario_argument(
                '-n', '--scenario-name', '--name',
                help='name of the scenario to launch')

        parsers = self.parser.add_subparsers(title='actions', metavar='action')
        parsers.required = False

        parser = parsers.add_parser(
                'run', help='run the selected scenario on the controller '
                'after optionally sending it (default action)')
        # Ensure we keep a reference to this parser before overriding the variable latter on
        get_defaults = parser.parse_args
        self.parser.set_defaults(_action=lambda builder=None: self._default_action(get_defaults([]), builder))

        self.run_group = parser.add_argument_group('scenario arguments')
        group = parser.add_argument_group('collector')
        group.add_argument(
                '-c', '--collector-address', '--collector', metavar='ADDRESS',
                help='IP address of the collector. If empty, will '
                'assume the collector is on the controller')
        group.add_argument(
                '-e', '--elasticsearch-port',
                type=int, default=9200, metavar='PORT',
                help='port on which the ElasticSearch service is listening')
        group.add_argument(
                '-i', '--influxdb-port',
                type=int, default=8086, metavar='PORT',
                help='port on which the InfluxDB query service is listening')
        group.add_argument(
                '-d', '--database-name', default='openbach', metavar='NAME',
                help='name of the InfluxDB database where statistics are stored')
        group.add_argument(
                '-t', '--time', '--epoch', default='ms', metavar='UNIT',
                help='unit of time for data returned by the InfluxDB API')
        parser.set_defaults(_action=self._launch_and_wait)
        group = parser.add_argument_group('scenario instance data')
        group.add_argument(
                '--data', dest='path', metavar='PATH', type=Path, const=Path(), nargs='?',
                help='Fetch scenario instance data after running it. If path is '
                'specified, store the file there instead of the current directory.')
        group.add_argument(
                '--file', '--add-file', action='append', default=[],
                nargs=2, metavar=('JOB_NAME', 'STAT_NAME'),
                help='include the files generated by the given statistic '
                'of the given job into the downloaded tarball.')
        group = parser.add_argument_group('settings')
        group.add_argument(
                '--no-logs', dest='logs', action='store_false',
                help='Disable log retrieval at the end of a scenario.')
        group.add_argument(
                '--poll-waiting-time', type=float, default=self.WAITING_TIME_BETWEEN_STATES_POLL,
                help='Waiting time in seconds between states poll when monitoring scenario completion.')

        parser = parsers.add_parser(
                'build', help='write the JSON of the selected '
                'scenario into the given directory')
        parser.add_argument(
                'json_path', metavar='PATH',
                help='path to a directory to store generated JSON files')
        parser.add_argument(
                '--local', '--no-controller',
                dest='contact_controller', action='store_false',
                help='do not try to contact the controller to fetch '
                'or update information; use the provided scenario '
                'builder (if any) instead.')
        parser.set_defaults(_action=self._write_json)

    def add_scenario_argument(
            self, *name_or_flags, action=None, nargs=None,
            const=None, default=None, type=None, choices=None,
            required=None, help=None, metavar=None, dest=None):
        kwargs = {
                'action': action,
                'nargs': nargs,
                'const': const,
                'default': default,
                'type': type,
                'choices': choices,
                'required': required,
                'help': help,
                'metavar': metavar,
                'dest': dest,
        }
        kwargs = {key: value for key, value in kwargs.items() if value is not None}
        self.scenario_group.add_argument(*name_or_flags, **kwargs)

    def add_run_argument(
            self, *name_or_flags, action=None, nargs=None,
            const=None, default=None, type=None, choices=None,
            required=None, help=None, metavar=None, dest=None):
        kwargs = {
                'action': action,
                'nargs': nargs,
                'const': const,
                'default': default,
                'type': type,
                'choices': choices,
                'required': required,
                'help': help,
                'metavar': metavar,
                'dest': dest,
        }
        kwargs = {key: value for key, value in kwargs.items() if value is not None}
        action = self.run_group.add_argument(*name_or_flags, **kwargs)
        self._default_arguments[action.dest] = action.default

    def parse(self, args=None, default_scenario_name=' *** Generated Scenario *** '):
        if args is not None:
            logging.getLogger(__name__).debug(
                    'Scenario observer parsing from script-provided arguments: %s',
                    args)
        args = super().parse(args)
        if args.scenario_name is None:
            args.scenario_name = default_scenario_name
        return args

    parse_args = parse

    def launch_and_wait(self, builder=None):
        if not hasattr(self, 'args'):
            self.parse()

        return self.args._action(builder)

    def _send_scenario_to_controller(self, builder=None):
        if builder is None:
            scenario_getter = self.share_state(GetScenario)
            scenario = scenario_getter.execute(False)
            scenario.raise_for_status()
        else:
            scenarios_getter = self.share_state(ListScenarios)
            scenarios = scenarios_getter.execute(False)
            scenarios.raise_for_status()
            scenarios = {scenario['name'] for scenario in scenarios.json()}

            self.args.scenario_name = str(builder)
            scenario_setter = self.share_state(CreateScenario)
            scenario_modifier = self.share_state(ModifyScenario)
            for scenario in builder.subscenarios:
                scenario_name = str(scenario)
                if scenario_name in scenarios:
                    scenario_modifier.args.scenario_name = scenario_name
                    scenario_modifier.args.scenario = scenario.build()
                    scenario = scenario_modifier.execute(False)
                else:
                    scenarios.add(scenario_name)
                    scenario_setter.args.scenario = scenario.build()
                    scenario = scenario_setter.execute(False)
                scenario.raise_for_status()

    def _run_scenario_to_completion(self):
        scenario_starter = self.share_state(StartScenarioInstance)
        response = scenario_starter.execute(False)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            self.parser.error('{}:\n{}'.format(error, json.dumps(response.json(), indent=4)))
        scenario_id = response.json()['scenario_instance_id']

        scenario_waiter = self.share_state(StatusScenarioInstance)
        scenario_waiter.args.scenario_instance_id = scenario_id
        retries_left = MAX_RETRIES_STATUS
        while True:
            time.sleep(self.args.poll_waiting_time)
            response = scenario_waiter.execute(False).json()
            status = response.get('status')
            if status is None:
                retries_left -= 1
                if not retries_left:
                    self.parser.error('scenario instance status could not be fetched')
                logging.getLogger(__name__).warning(
                        'Error while fetching scenario status:\n%s\n\n%d retries left',
                        PprintFormatter(response), retries_left)
            elif status in ('Finished Ko',):
                self.parser.error('scenario instance failed (status is \'{}\')'.format(status))
            elif status in ('Finished', 'Finished Ok', 'Stopped'):
                break
            else:
                retries_left = MAX_RETRIES_STATUS

        if self.args.path is not None:
            data_fetcher = self.share_state(GetScenarioInstanceData)
            data_fetcher.args.scenario_instance_id = scenario_id
            data_fetcher.execute(False)

        return response

    def _launch_and_wait(self, builder=None):
        if self.args.collector_address is None:
            self.args.collector_address = self.args.controller

        if not hasattr(self.args, 'argument'):
            self.args.argument = {
                name: getattr(self.args, name, value)
                for name, value in self._default_arguments.items()
            }

        begin_date = int(time.time()) * 1000  # Flooring to the last second
        try:
            self._send_scenario_to_controller(builder)
            self._last_instance = self._run_scenario_to_completion()
        finally:
            if self.args.logs:
                end_date = int(time.time() * 1000)  # Flooring to the last millisecond

                sleep_duration = 1
                elasticsearch = ElasticSearchConnection(self.args.collector_address, self.args.elasticsearch_port)
                with suppress(requests.exceptions.BaseHTTPError, LookupError, ValueError):
                    settings = elasticsearch.settings_query("index.refresh_interval")
                    intervals = (settings[index]["settings"]["index"]["refresh_interval"] for index in settings)
                    sleep_duration = max(map(_convert_time, intervals), default=sleep_duration)

                logger = logging.getLogger(__name__)
                logger.info('Retrieving logs if any, wait during logstash refreshing (%ds) ...', sleep_duration)
                time.sleep(sleep_duration)
                response = elasticsearch.all_logs(timestamps=(begin_date, end_date))
                for log in response:
                    logger.error('%s', PprintFormatter(log))
        return self._last_instance

    def _write_json(self, builder=None):
        path = Path(self.args.json_path).absolute()
        path.mkdir(parents=True, exist_ok=True)

        if self.args.contact_controller:
            self._send_scenario_to_controller(builder)
            scenario_getter = self.share_state(GetScenario)
            scenarios = [self.args.scenario_name] if builder is None else builder.subscenarios
            for scenario in scenarios:
                scenario_getter.args.scenario_name = str(scenario)
                scenario = scenario_getter.execute(False)
                scenario.raise_for_status()
                content = scenario.json()
                name = '{}.json'.format(content['name'])
                with open(str(path / name), 'w') as fp:
                    json.dump(content, fp, indent=4)
        elif builder:
            for scenario in builder.subscenarios:
                name = '{}.json'.format(scenario)
                scenario.write(str(path / name))
        else:
            self.parser.error(
                    'asked to *not* contact the controller without a provided '
                    'scenario builder: cannot create scenario file')

    def _default_action(self, defaults, builder=None):
        for name, value in vars(defaults).items():
            setattr(self.args, name, value)

        self.args._action(builder)


class DataProcessor:
    """Helper class that retrieves data from scenario instances
    and ease information extraction.
    """
    def __init__(self, observer, scenario_instance=None):
        """Associate this instance to a ScenarioObserver in order
        to access a collector. Optionally associate a scenario instance
        or get the last instance of the collector if not.
        """
        if scenario_instance is None:
            scenario_instance = observer._last_instance

        self._post_processing = {}
        self._instance = scenario_instance
        self._collector = CollectorConnection(
                observer.args.collector_address,
                observer.args.elasticsearch_port,
                observer.args.influxdb_port,
                observer.args.database_name,
                observer.args.time)

    @property
    def instance(self):
        return self._instance

    @instance.setter
    def instance(self, _instance):
        for attribute in ('scenario_name', 'scenario_instance_id', 'openbach_functions'):
            if attribute not in _instance:
                raise TypeError('instance is expected to be an OpenBach scenario instance')
        self._instance = _instance

    def add_callback(self, label, callback, openbach_functions):
        """Register a callback to be run on the data gathered from the collector.

        The data returned from the callback will be accessible under the provided
        label as a key in the returned dictionnary from the `post_processing` method.

        The `openbach_functions` to provide are a list of openbach function IDs
        going through the start_scenario_instance openbach functions down to the
        target start_job_instance openbach_function that the callback should
        operate on. This is meant to accept an entry from a call to the scenario
        builder's `Scenario.extract_function_id` call.
        """
        self._post_processing[tuple(openbach_functions)] = (label, callback)

    def _extract_callback(self, scenario_instance, parent_scenarios=()):
        for function in scenario_instance['openbach_functions']:
            parents = parent_scenarios + (function['id'],)
            with suppress(KeyError):
                yield from self._extract_callback(function['scenario'], parents)
            with suppress(KeyError):
                yield function['job']['id'], self._post_processing[parents]

    def post_processing(self):
        """Actually fetches the raw data from the collector and run callbacks on them"""
        callbacks = dict(self._extract_callback(self._instance))

        try:
            scenario, = self._collector.scenarios(scenario_instance_id=self._instance['scenario_instance_id'])
        except ValueError:
            exit('cannot retrieve scenario instance data from database')
        self._post_processing.clear()

        return {
                callbacks[job.instance_id][0]: callbacks[job.instance_id][1](job)
                for job in scenario.jobs if job.instance_id in callbacks
        }


class PprintFormatter:
    def __init__(self, obj, width=300):
        self.obj = obj
        self.width = width

    def __str__(self):
        return pprint.pformat(self.obj, width=self.width)


def _convert_time(duration):
    amount, unit = re.match('(\d+)(d$|h$|m$|s$|ms$)', duration).groups()
    unit = {'s': 'seconds', 'm': 'minutes', 'd': 'days', 'h': 'hours', 'ms': 'milliseconds'}[unit]
    return datetime.timedelta(**{unit: int(amount)}).total_seconds()
