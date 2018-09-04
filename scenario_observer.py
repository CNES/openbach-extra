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

import requests
from data_access import CollectorConnection

from frontend import FrontendBase, ActionFailedError
from create_scenario import CreateScenario
from get_scenario import GetScenario
from modify_scenario import ModifyScenario
from start_scenario_instance import StartScenarioInstance
from status_scenario_instance import StatusScenarioInstance


class ScenarioObserver(FrontendBase):
    def __init__(self, scenario, project=None, builder=None):
        super().__init__('OpenBACH — Run a scenario and postprocess stats')
        self.parser.add_argument(
                '-o', '--override', action='store_true',
                help='have the provided scenario builder (if any) replace the current scenario')

        group = self.parser.add_argument_group('collector')
        group.add_argument(
                '-c', '--collector', metavar='ADDRESS',
                help='IP address of the collector. If empty, will assume the collector is on the controller')
        group.add_argument(
                '-e', '--elasticsearch-port', type=int, default=9200, metavar='PORT',
                help='port on which the ElasticSearch service is listening')
        group.add_argument(
                '-i', '--influxdb-port', type=int, default=8086, metavar='PORT',
                help='port on which the InfluxDB query service is listening')
        group.add_argument(
                '-d', '--database-name', default='openbach', metavar='NAME',
                help='name of the InfluxDB database where statistics are stored')
        group.add_argument(
                '-t', '--time', '--epoch', default='ms', metavar='UNIT',
                help='unit of time for data returned by the InfluxDB API')

        group = self.parser.add_argument_group('scenario arguments')
        group.add_argument(
                '-a', '--argument', nargs=2, default=[], action='append',
                metavar=('NAME', 'VALUE'), help='value of an argument of the scenario')

        self.parse()
        self.args.name = scenario
        self.args.project = project
        if self.args.collector is None:
            self.args.collector = self.args.controller

        if builder is not None:
            self.args.scenario = builder.build()

        scenario_getter = self._share_state(GetScenario)
        try:
            scenario = scenario_getter.execute(False)
            scenario.raise_for_status()
        except Exception:
            scenario_setter = self._share_state(CreateScenario)
            scenario = scenario_setter.execute(False)
        else:
            if self.args.override:
                scenario_modifier = self._share_state(ModifyScenario)
                scenario = scenario_modifier.execute(False)

        scenario.raise_for_status()
        self.scenario = scenario.json()
        self._scenario = {
                function['label']: function['id']
                for function in self.scenario['openbach_functions']
                if 'start_job_instance' in function and function['label']
        }
        self._post_processing = {}

    def _share_state(self, script_cls):
        instance = script_cls()
        instance.session = self.session
        instance.base_url = self.base_url
        instance.args = self.args
        return instance

    def post_processing(self, label, callback, *, ignore_missing_label=False):
        try:
            function_id = self._scenario[label]
        except KeyError:
            if not ignore_missing_label:
                self.parser.error('missing openbach function labeled \'{}\''.format(label))
        else:
            self._post_processing[function_id] = (label, callback)

    def launch_and_wait(self):
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

        callbacks = {
                function['job']['id']: self._post_processing[function['id']]
                for function in response['openbach_functions']
                if function['id'] in self._post_processing
        }

        collector = CollectorConnection(
                self.args.collector,
                self.args.elasticsearch_port,
                self.args.influxdb_port,
                self.args.database_name,
                self.args.time,
        )
        try:
            scenario, = collector.scenarios(scenario_instance_id=scenario_id)
        except ValueError:
            self.parser.error('cannot retrieve scenario instance data from database')

        return {
                callbacks[job.instance_id][0]: callbacks[job.instance_id][1](job)
                for job in scenario.jobs if job.instance_id in callbacks
        }
