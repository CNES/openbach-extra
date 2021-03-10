#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2020 CNES
#
#
#   This file is part of the OpenBACH testbed.
#
#
#   OpenBACH is a free software : you can redistribute it and/or modify it under
#   the terms of the GNU General Public License as published by the Free Software
#   Foundation, either version 3 of the License, or (at your option) any later
#   version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
#   details.
#
#   You should have received a copy of the GNU General Public License along with
#   this program. If not, see http://www.gnu.org/licenses/.

import argparse 
import ipaddress
import time
from pathlib import Path
from itertools import chain

from auditorium_scripts.push_file import PushFile
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder import Scenario
from scenario_builder.helpers.utils import Validate, ValidateOptional, patch_print_help
from scenario_builder.helpers.access import opensand
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.scenarios import opensand_run, opensand_net_conf, opensand_satcom_conf


SCENARIO_NAME = 'Opensand'


class Entity:
    def __init__(
            self, entity, infrastructure, topology,
            profile, bridge_to_lan, tap_name='opensand_tap',
            bridge_name='opensand_br', tap_mac_address=None):
        self.entity = entity
        self.infrastructure = infrastructure
        self.topology = topology
        self.profile = profile
        self.bridge_to_lan = bridge_to_lan
        self.tap_name = tap_name
        self.bridge_name = bridge_name
        self.tap_mac = tap_mac_address


class Satellite:
    def __init__(self, entity, infrastructure, topology):
        self.entity = entity
        self.infrastructure = infrastructure
        self.topology = topology


class ValidateSatellite(argparse.Action):
    def __call__(self, parser, args, values, option_string=None): 
        satellite = Satellite(*values)
        setattr(args, self.dest, satellite)


class ValidateGroundEntity(ValidateOptional, Validate):
    ENTITY_TYPE = Entity


def _extract_config_filepath(entity, file_type):
    path = getattr(entity, file_type, None)
    if path is None:
        name = file_type + '.xml'
    else:
        name = Path(path).name

    return Path('/etc/opensand', name).as_posix()


def example_opensand(satellite, ground_entities, duration=0, post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, '')

    network_entities = [
            opensand_net_conf.OPENSAND_ENTITY(
                terrestrial.entity,
                terrestrial.tap_mac_address,
                terrestrial.tap_name,
                terrestrial.bridge_name,
                terrestrial.bridge_to_lan,
            )
            for terrestrial in ground_entities
    ]
    network_configure = scenario.add_function('start_scenario_instance')
    network_configure.configure(opensand_net_conf.build(network_entities, 'configure'))

    wait = [network_configure]
    # TODO: handle having files already pushed on agents
    push_files = scenario.add_function('start_scenario_instance', wait_finished=[network_configure])
    push_files.configure(opensand_satcom_conf.build(satellite, ground_entities)
    wait.append(push_files)

    run_satellite = opensand_run.SAT(
        satellite.entity,
        _extract_config_filepath(satellite, 'infrastructure'),
        _extract_config_filepath(satellite, 'topology'))
    run_entities = [
        opensand_run.GROUND(
            entity.entity,
            _extract_config_filepath(entity, 'infrastructure'),
            _extract_config_filepath(entity, 'topology'),
            _extract_config_filepath(entity, 'profile'))
        for entity in ground_entities
    ]
    run = scenario.add_function('start_scenario_instance', wait_finished=wait)
    run.configure(opensand_run.build(run_satellite, run_entities, duration))

    network_delete = scenario.add_function('start_scenario_instance', wait_finished=[run])
    network_delete.configure(opensand_net_conf.build(network_entities, 'delete', opensand_net_conf.SCENARIO_NAME + '_delete'))

    if post_processing_entity:
        post_processed = list(scenario.extract_function_id(opensand=opensand.opensand_find_ground, include_subscenarios=True))
        if post_processed:
            time_series_on_same_graph(
                    scenario,
                    post_processing_entity,
                    post_processed,
                    [['up_return_modcod.sent_modcod']],
                    [['Sent ModCod (id)']],
                    [['UP/Return ModCod']],
                    [['Entity {} - ModCod'.format(entity.entity) for entity in ground_entities]],
                    False, [network_delete], None, 2)

            time_series_on_same_graph(
                    scenario,
                    post_processing_entity,
                    post_processed,
                    [['throughputs.l2_from_sat.total']],
                    [['Throughput from satellite (kbps)']],
                    [['Thoughput']],
                    [['Entity {} - Throughput from satellite'.format(e.entity) for e in ground_entities]],
                    False, [network_delete], None, 2)
            cdf_on_same_graph(
                    scenario,
                    post_processing_entity,
                    post_processed,
                    100,
                    [['throughputs.l2_from_sat.total']],
                    [['Throughput from satellite (kbps)']],
                    [['Thoughput']],
                    [['Entity {} - Throughput from satellite'.format(e.entity) for e in ground_entities]],
                    False, [network_delete], None, 2)

    return scenario


def send_files_to_controller(pusher, entity, prefix='opensand'):
    name = entity.entity
    destination = Path(prefix, name)
    files = [
            getattr(entity, f)
            for f in ('infrastructure', 'topology', 'profile')
            if hasattr(entity, f)
    ]

    for config_file in map(Path, files):
        with folder.joinpath(config_file).open() as local_file:
            pusher.args.local_file = local_file
            pusher.args.remote_path = (destination / config_file.name).as_posix()
            pusher.execute(False)
        # If we don't use this, the controller has a tendency to close the
        # connection after some files, so slowing things down the dirty way.
        time.sleep(0.1)

    for f in ('infrastructure', 'topology', 'profile'):
        if hasattr(entity, f):
            setattr(entity, f, Path(getattr(entity, f)).name)


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--satellite', '--sat', '-s',
            required=True, action=ValidateSatellite, nargs=3,
            metavar=('ENTITY', 'INFRASTRUCTURE_PATH', 'TOPOLOGY_PATH'),
            help='The satellite of the platform. Must be supplied only once.')
    observer.add_scenario_argument(
            '--ground-entity', '--ground', '--entity', '-g', '-e',
            required=True, action=ValidateGroundEntity, nargs=4,
            metavar=('ENTITY', 'INFRASTRUCTURE_PATH', 'TOPOLOGY_PATH', 'PROFILE_PATH'),
            help='A ground entity in the platform. Must be supplied at least once.')
    observer.add_scenario_argument(
            '--duration', '-d', required=False, default=0, type=int,
            help='Duration of the opensand run test, leave blank for endless emulation.')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, SCENARIO_NAME)

    pusher = observer._share_state(PushFile)
    pusher.args.keep = True
    send_files_to_controller(pusher, args.satellite)
    for entity in args.ground_entity:
        send_files_to_controller(pusher, entity)

    scenario = example_opensand(
            args.satellite,
            args.ground_entity,
            args.duration,
            args.post_processing_entity,
            scenario_name=args.scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
