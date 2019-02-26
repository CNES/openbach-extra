#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2018 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.


"""Framework for easier Scenario postprocessing"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''

import time
import json
from pathlib import Path
from contextlib import suppress

import requests
from data_access import CollectorConnection

from auditorium_scripts.frontend import FrontendBase
from auditorium_scripts.create_scenario import CreateScenario
from auditorium_scripts.get_scenario import GetScenario
from auditorium_scripts.modify_scenario import ModifyScenario
from auditorium_scripts.start_scenario_instance import StartScenarioInstance
from auditorium_scripts.status_scenario_instance import StatusScenarioInstance


class ScenarioObserver(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Run a scenario and postprocess stats')
        self._post_processing = {}
        self._scenarios = {}
        self.build_parser()

    def build_parser(self):
        self.parser.add_argument(
                '-o', '--override', action='store_true',
                help='have the provided scenario builder '
                '(if any) replace the current scenario')

        self.scenario_group = self.parser.add_argument_group('scenario arguments')
        self.add_scenario_argument(
                '-n', '--name', '--scenario-name',
                help='name of the scenario to launch')
        self.add_scenario_argument(
                '-p', '--project', '--project-name', metavar='NAME',
                help='name of the project the scenario is associated with')

        self.parser.set_defaults(_action=self._launch_and_wait)
        parsers = self.parser.add_subparsers(title='actions', metavar='action')
        parsers.required = False

        parser = parsers.add_parser(
                'run', help='run the selected scenario on the controller '
                'after optionally sending it (default action)')
        group = parser.add_argument_group('collector')
        group.add_argument(
                '-c', '--collector', metavar='ADDRESS',
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

    def post_processing(self, label, callback, *, subscenario=None, ignore_missing_label=False):
        if subscenario is None:
            subscenario = self.args.name

        try:
            function_id = self._scenarios[subscenario][label]
        except KeyError:
            if not ignore_missing_label:
                self.parser.error('missing openbach function labeled \'{}\' in scenario \'{}\''.format(label, subscenario))
        else:
            self._post_processing[(subscenario, function_id)] = (label, callback)

    def parse(self, args=None, default_scenario_name=' *** Generated Scenario *** '):
        args = super().parse(args)
        if args.name is None:
            args.name = default_scenario_name
        return args

    parse_args = parse

    def launch_and_wait(self, builder=None):
        if not hasattr(self, 'args'):
            self.parse()

        return self.args._action(builder)

    def _share_state(self, script_cls):
        instance = script_cls()
        instance.session = self.session
        instance.base_url = self.base_url
        instance.args = self.args
        return instance

    def _extract_scenario_json(self, scenario):
        self._scenarios[self.args.name] = {
                function['label']: function['id']
                for function in scenario.json()['openbach_functions']
                if 'start_job_instance' in function and function['label']
        }

    def _extract_callback(self, scenario_instance):
        name = scenario_instance['scenario_name']
        for function in scenario_instance['openbach_functions']:
            with suppress(KeyError):
                yield from self._extract_callback(function['scenario'])
            with suppress(KeyError):
                callback = self._post_processing[(name, function['id'])]
                yield function['job']['id'], callback

    def _send_scenario_to_controller(self, builder=None):
        scenario_getter = self._share_state(GetScenario)
        if builder is None:
            scenario = scenario_getter.execute(False)
            scenario.raise_for_status()
            self._extract_scenario_json(scenario)
        else:
            scenario_setter = self._share_state(CreateScenario)
            scenario_modifier = self._share_state(ModifyScenario)
            for scenario in builder.subscenarios:
                self.args.name = str(scenario)
                self.args.scenario = scenario.build()

                try:
                    scenario = scenario_getter.execute(False)
                    scenario.raise_for_status()
                except Exception:
                    scenario = scenario_setter.execute(False)
                else:
                    if self.args.override:
                        scenario = scenario_modifier.execute(False)
                scenario.raise_for_status()
                self._extract_scenario_json(scenario)

    def _run_scenario_to_completion(self):
        scenario_starter = self._share_state(StartScenarioInstance)
        response = scenario_starter.execute(False)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            self.parser.error('{}:\n{}'.format(error, json.dumps(response.json(), indent=4)))
        scenario_id = response.json()['scenario_instance_id']

        scenario_waiter = self._share_state(StatusScenarioInstance)
        scenario_waiter.args.instance_id = scenario_id
        while True:
            time.sleep(self.WAITING_TIME_BETWEEN_STATES_POLL)
            response = scenario_waiter.execute(False).json()
            status = response['status']
            if status in ('Finished KO', 'Stopped'):
                self.parser.error('scenario instance failed (status is \'{}\')'.format(status))
            if status in ('Finished', 'Finished OK'):
                break

        return response

    def _launch_and_wait(self, builder=None):
        if self.args.collector is None:
            self.args.collector = self.args.controller

        if not hasattr(self.args, 'argument'):
            self.args.argument = {}

        self._send_scenario_to_controller(builder)
        scenario_instance = self._run_scenario_to_completion()
        callbacks = dict(self._extract_callback(scenario_instance))
        collector = CollectorConnection(
                self.args.collector,
                self.args.elasticsearch_port,
                self.args.influxdb_port,
                self.args.database_name,
                self.args.time,
        )
        try:
            scenario, = collector.scenarios(scenario_instance_id=scenario_instance['scenario_instance_id'])
        except ValueError:
            self.parser.error('cannot retrieve scenario instance data from database')

        return {
                callbacks[job.instance_id][0]: callbacks[job.instance_id][1](job)
                for job in scenario.jobs if job.instance_id in callbacks
        }

    def _write_json(self, builder=None):
        path = Path(self.args.json_path).absolute()
        path.mkdir(parents=True, exist_ok=True)

        if self.args.contact_controller:
            self._send_scenario_to_controller(builder)
            scenario_getter = self._share_state(GetScenario)
            scenarios = [self.args.name] if builder is None else builder.subscenarios
            for scenario in scenarios:
                self.args.name = str(scenario)
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
