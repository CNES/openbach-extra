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

"""This executor runs an OpenSAND scenario allowing to: 
 - Push opensand configuration files from the controller to the agents /etc/opensand folder
 - Filter the files sent depending on the type of the receiving entity
This step is necessary to push the OpenSAND configuration of a platform.
"""

import time
from pathlib import Path

from auditorium_scripts.push_file import PushFile
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import opensand_satcom_conf


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
            '--topology', '-t',
            help='The common topology file to push to all entities.')
    observer.add_scenario_argument(
            '--satellite', '--sat', '-s',
            nargs=2, metavar=('ENTITY', 'INFRASTRUCTURE_PATH'),
            help='The entity running the satellite of the platform.')
    observer.add_scenario_argument(
            '--satellite-no-conf', '-S', metavar='ENTITY',
            help='The entity running the satellite of the platform. '
            'Use this option if the infrastructure configuration file is '
            'already present and you do not wish to push a new one.')
    observer.add_scenario_argument(
            '--ground-entity', '--ground', '--entity', '-g', '-e',
            nargs=3, action='append', default=[],
            metavar=('ENTITY', 'INFRASTRUCTURE_PATH', 'PROFILE_PATH'),
            help='An entity running a GW or ST in the platform. '
            'Can be supplied several times.')
    observer.add_scenario_argument(
            '--ground-entity-no-conf', '--entity-no-conf', '-E',
            action='append', metavar='ENTITY', default=[],
            help='An entity running a GW or ST in the platform. Use this '
            'option if the infrastructure and profile configuration files '
            'are already present and you do not wish to push new ones. Can '
            'be supplied several times.')
    observer.add_scenario_argument(
            '--ground-entity-no-infra', '--entity-no-infra', '-I',
            action='append', nargs=2, default=[],
            metavar=('ENTITY', 'PROFILE_PATH'),
            help='An entity running a GW or ST in the platform. Use this '
            'option if the infrastructure configuration file is '
            'already present and you do not wish to push a new one. Can '
            'be supplied several times.')
    observer.add_scenario_argument(
            '--ground-entity-no-profile', '--entity-no-profile', '-P',
            action='append', nargs=2, default=[],
            metavar=('ENTITY', 'INFRASTRUCTURE_PATH'),
            help='An entity running a GW or ST in the platform. Use this '
            'option if the profile configuration file is '
            'already present and you do not wish to push a new one. Can '
            'be supplied several times.')

    args = observer.parse(argv, opensand_satcom_conf.SCENARIO_NAME)
    if args.satellite is not None and args.satellite_no_conf is not None:
        observer.parser.error('argument --satellite-no-conf: not allowed with argument --satellite')

    opensand_entities = []
    #Store files on the controller
    pusher = observer.share_state(PushFile)
    pusher.args.keep = True
    if args.satellite:
        name, infrastructure = args.satellite
        opensand_entities.append(opensand_satcom_conf.OpensandEntity(
            name,
            send_files_to_controller(pusher, name, infrastructure),
            send_files_to_controller(pusher, name, args.topology)))
    if args.satellite_no_conf:
        name = args.satellite_no_conf
        opensand_entities.append(opensand_satcom_conf.OpensandEntity(
            name,
            None,
            send_files_to_controller(pusher, name, args.topology)))
    for name, infrastructure, profile in args.ground_entity:
        opensand_entities.append(opensand_satcom_conf.OpensandEntity(
            name,
            send_files_to_controller(pusher, name, infrastructure),
            send_files_to_controller(pusher, name, args.topology),
            send_files_to_controller(pusher, name, profile)))
    for name in args.ground_entity_no_conf:
        opensand_entities.append(opensand_satcom_conf.OpensandEntity(
            name,
            None,
            send_files_to_controller(pusher, name, args.topology),
            None))
    for name, profile in args.ground_entity_no_infra:
        opensand_entities.append(opensand_satcom_conf.OpensandEntity(
            name,
            None,
            send_files_to_controller(pusher, name, args.topology),
            send_files_to_controller(pusher, name, profile)))
    for name, infrastructure in args.ground_entity_no_profile:
        opensand_entities.append(opensand_satcom_conf.OpensandEntity(
            name,
            send_files_to_controller(pusher, name, infrastructure),
            send_files_to_controller(pusher, name, args.topology),
            None))


    scenario = opensand_satcom_conf.build(opensand_entities)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
