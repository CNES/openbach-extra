#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2023 CNES
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

"""Detailed description of the scenario.

This scenarios enables to configure the entities and run a full OpenSAND test.
It is based on the scenarios opensand_net_conf, opensand_satcom_conf and opensand_run.
Check the following link for further information about those scenarios : https://github.com/CNES/openbach-extra/blob/master/executors/references/README.md


# Step-by-step description of the scenario :
    1. Parse the paths of the configuration files entered in the parameters
    2. Send those files to the OpenBACH Controller
    3. Launch opensand_net_conf to create and set the necessary bridges and TAP interfaces inside the ground entities (GWs and STs)
    4. Launch opensand_satcom_conf to push all the configuration files from the controller to each corresponding entity
    5. Launch opensand_run to run an OpenSAND test (start the entities and start the OpenSAND services)
    6. Launch opensand_net_conf to clean the network configuration 


# Some words about the helper functions used in this example :
    - The function 'send_files_to_controller' is used to send the configuration files from the local machine to the controller (step 2)
    - The function '_extract_config_filepath' allows to get the configuration file inside the entity (step 5)


# Parameters description :
  A detailed description of the parameters with examples is available in the following link:
  https://github.com/CNES/openbach-extra/tree/master/externals_jobs/stable_jobs/access/opensand

  Note : if a configuration files is not set, the entity will load the one saved at :
  /etc/opensand/{infrastructure,topology,profile}.xml to run OpenSAND


# Generated test reports:
    - The evolution of the the MODCOD used by the GW(s) and the ST(s)
    - The evolution of the throughput from the Satellite (kbps)
    - The CDF of the throughput from the Satellite (kbps)
"""

import time
import argparse 
import ipaddress
from pathlib import Path
from dataclasses import dataclass

from auditorium_scripts.push_file import PushFile
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder import Scenario
from scenario_builder.helpers.utils import Validate, ValidateOptional, patch_print_help
from scenario_builder.helpers.access import opensand
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.scenarios import opensand_run, opensand_net_conf, opensand_satcom_conf


SCENARIO_NAME = 'Opensand'
SCENARIO_DESCRIPTION = """This scenarios enables to run a full OpenSAND experiment. It runs the following sub-scenarios :
- The opensand_net_conf scenario is used to configure the network 
- The opensand_satcom_conf scenario is used to deploy an OpenSAND configuration
- The opensand_run scenario is used to start the entities and start the service
"""

@dataclass(frozen=True)
class OpensandEntity(opensand_satcom_conf.OpensandEntity, opensand_net_conf.OpensandEntity):
    pass


@dataclass(frozen=True)
class Satellite:
    entity: str
    infrastructure: str = None


@dataclass(frozen=True)
class Entity:
    entity: str
    infrastructure: str
    profile: str
    bridge_to_lan: str
    tap_name: str = 'opensand_tap'
    bridge_name: str = 'opensand_br'
    tap_mac_address: str = None


@dataclass(frozen=True)
class EntityNoProfile:
    entity: str
    infrastructure: str
    bridge_to_lan: str
    tap_name: str = 'opensand_tap'
    bridge_name: str = 'opensand_br'
    tap_mac_address: str = None


@dataclass(frozen=True)
class EntityNoInfrastructure:
    entity: str
    profile: str
    bridge_to_lan: str
    tap_name: str = 'opensand_tap'
    bridge_name: str = 'opensand_br'
    tap_mac_address: str = None


@dataclass(frozen=True)
class EntityNoConfiguration:
    entity: str
    bridge_to_lan: str
    tap_name: str = 'opensand_tap'
    bridge_name: str = 'opensand_br'
    tap_mac_address: str = None


class ValidateSatellite(ValidateOptional, argparse.Action):
    def __call__(self, parser, args, values, option_string=None): 
        satellite = Satellite(*values)
        setattr(args, self.dest, satellite)


class ValidateGroundEntity(ValidateOptional, Validate):
    ENTITY_TYPE = Entity


class ValidateGroundEntityNP(ValidateOptional, Validate):
    ENTITY_TYPE = EntityNoProfile


class ValidateGroundEntityNI(ValidateOptional, Validate):
    ENTITY_TYPE = EntityNoInfrastructure


class ValidateGroundEntityNC(ValidateOptional, Validate):
    ENTITY_TYPE = EntityNoConfiguration


def _extract_config_filepath(entity, file_type):
    path = getattr(entity, file_type, None)
    name = (file_type + '.xml') if path is None else Path(path).name
    return Path('/etc/opensand', name).as_posix()


def example_opensand(satellite, ground_entities, duration=0, post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, '')

    network_configure = scenario.add_function('start_scenario_instance')
    network_configure.configure(opensand_net_conf.build(ground_entities, 'configure'))
    wait = [network_configure]

    files_to_push = [
            entity for entity in ground_entities
            if entity.infrastructure is not None or entity.topology is not None or entity.profile is not None
    ]
    if satellite.infrastructure is not None or satellite.topology is not None:
        files_to_push.append(satellite)

    if files_to_push:
        push_files = scenario.add_function('start_scenario_instance', wait_finished=[network_configure])
        push_files.configure(opensand_satcom_conf.build(files_to_push))
        wait = [push_files]

    run_satellite = opensand_run.Satellite(
        satellite.entity,
        _extract_config_filepath(satellite, 'infrastructure'),
        _extract_config_filepath(satellite, 'topology'))
    run_entities = [
        opensand_run.GroundEntity(
            entity.entity,
            _extract_config_filepath(entity, 'infrastructure'),
            _extract_config_filepath(entity, 'topology'),
            _extract_config_filepath(entity, 'profile'))
        for entity in ground_entities
    ]
    run = scenario.add_function('start_scenario_instance', wait_finished=wait)
    run.configure(opensand_run.build(run_satellite, run_entities, duration))

    network_delete = scenario.add_function('start_scenario_instance', wait_finished=[run])
    network_delete.configure(opensand_net_conf.build(ground_entities, 'delete', opensand_net_conf.SCENARIO_NAME + '_delete'))

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


def send_files_to_controller(pusher, entity, filepath, prefix=Path('opensand')):
    if filepath is None:
        return

    config_file = Path(filepath)
    destination = prefix / entity / config_file.name
    with config_file.open() as local_file:
        pusher.args.local_file = local_file
        pusher.args.remote_path = destination.as_posix()
        pusher.execute(False)
    # If we don't use this, the controller has a tendency to close the
    # connection after some files, so slowing things down the dirty way.
    time.sleep(0.1)

    return destination


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--satellite', '--sat', '-s',
            required=True, action=ValidateSatellite, nargs='*',
            metavar='ENTITY [INFRASTRUCTURE_PATH]',
            help='The satellite of the platform. Must be supplied only once.')
    observer.add_scenario_argument(
            '--topology', '-t',
            help='The common topology file to push to all entities. Optional '
            'in case /etc/opensand/topology.xml is already present on the agents.')
    observer.add_scenario_argument(
            '--ground-entity', '--ground', '--entity', '-g', '-e',
            dest='ground_entities', action=ValidateGroundEntity, nargs='*',
            metavar='ENTITY INFRASTRUCTURE_PATH PROFILE_PATH (BRIDGE_ADDRESS_MASK | '
            'BRIDGE_INTERFACE) [TAP_NAME [BRIDGE_NAME [TAP_MAC]]]',
            help='A ground entity in the platform. Must be supplied at least once.')
    observer.add_scenario_argument(
            '--ground-entity-no-profile', '-P',
            dest='ground_entities', action=ValidateGroundEntityNP, nargs='*',
            metavar='ENTITY INFRASTRUCTURE_PATH (BRIDGE_ADDRESS_MASK | '
            'BRIDGE_INTERFACE) [TAP_NAME [BRIDGE_NAME [TAP_MAC]]]',
            help='A ground entity in the platform. Use this option instead of '
            '--ground-entity if you wish to reuse an /etc/opensand/profile.xml '
            'file already present on the agent.')
    observer.add_scenario_argument(
            '--ground-entity-no-infrastructure', '-I',
            dest='ground_entities', action=ValidateGroundEntityNI, nargs='*',
            metavar='ENTITY PROFILE_PATH (BRIDGE_ADDRESS_MASK | '
            'BRIDGE_INTERFACE) [TAP_NAME [BRIDGE_NAME [TAP_MAC]]]',
            help='A ground entity in the platform. Use this option instead of '
            '--ground-entity if you wish to reuse an /etc/opensand/infrastructure.xml '
            'file already present on the agent.')
    observer.add_scenario_argument(
            '--ground-entity-no-configuration', '-E',
            dest='ground_entities', action=ValidateGroundEntityNC, nargs='*',
            metavar='ENTITY (BRIDGE_ADDRESS_MASK | BRIDGE_INTERFACE) '
            '[TAP_NAME [BRIDGE_NAME [TAP_MAC]]]',
            help='A ground entity in the platform. Use this option instead of '
            '--ground-entity if you wish to reuse both /etc/opensand/'
            '{infrastructure,profile}.xml files already present on the agent.')
    observer.add_scenario_argument(
            '--duration', '-d', required=False, default=0, type=int,
            help='Duration of the opensand run test, leave blank for endless emulation.')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')

    patch_print_help(observer.parser)
    args = observer.parse(argv, SCENARIO_NAME)

    pusher = observer._share_state(PushFile)
    pusher.args.keep = True

    satellite = [
            opensand_satcom_conf.OpensandEntity(
                args.satellite.entity,
                send_files_to_controller(pusher, args.satellite.entity, args.satellite.infrastructure),
                send_files_to_controller(pusher, args.satellite.entity, args.topology))
    ]

    ground_entities = [
            OpensandEntity(
                entity.entity,
                entity.tap_mac_address,
                entity.tap_name,
                entity.bridge_name,
                entity.bridge_to_lan,
                entity.entity,
                send_files_to_controller(pusher, entity.entity, getattr(entity, 'infrastructure', None)),
                send_files_to_controller(pusher, entity.entity, args.topology),
                send_files_to_controller(pusher, entity.entity, getattr(entity, 'profile', None)))
            for entity in args.ground_entities
    ]

    scenario = example_opensand(
            satellite,
            ground_entities,
            args.duration,
            args.post_processing_entity,
            scenario_name=args.scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
