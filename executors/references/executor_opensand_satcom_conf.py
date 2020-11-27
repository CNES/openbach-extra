#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016−2019 CNES
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


import time
import argparse 
import tempfile
from pathlib import Path

from auditorium_scripts.push_file import PushFile
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import opensand_satcom_conf


def send_files_to_controller(pusher, folder, prefix='opensand'):
    config_files = [
            p.relative_to(folder)
            for extension in ('conf', 'txt', 'csv', 'input')
            for p in folder.rglob('*.' + extension)
    ]

    for config_file in config_files:
        with folder.joinpath(config_file).open() as local_file:
            pusher.args.local_file = local_file
            pusher.args.remote_path = (prefix / config_file).as_posix()
            pusher.execute(False)
        # If we don't use this, the controller has a tendency to close the
        # connection after some files, so slowing things down the dirty way.
        time.sleep(0.1)

    return config_files


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument('satellite', help='The entity running the satellite of the platform.')
    observer.add_scenario_argument(
            '--configuration-folder', '-c', type=Path, metavar='FOLDER',
            help='Path to the configuration folder that should '
            'be dispatched on agents before the simulation.')
    observer.add_scenario_argument(
            '--extra-configuration-folder', '-e', nargs=2, action='append', default=[],
            metavar=('FOLDER', 'ENTITY'), help='Path to an extra configuration folder '
            'that should be dispatched to the specified entity before the simulation.')
    observer.add_scenario_argument(
            '--gateway', '-gw', action='append', default=[],
            help='The entity running a gateway in the platform. Can be supplied several times.')
    observer.add_scenario_argument(
            '--terminal', '--satellite-terminal', '-st', action='append', default=[],
            help='The entity running a satellite terminal in the platform. Can be supplied several times.')

    args = observer.parse(argv, opensand_satcom_conf.SCENARIO_NAME)

    if not args.configuration_folder and not args.extra_configuration_folder:
        observer.parser.error('one of the arguments --configuration-folder --extra-configuration-folder is required')

    #Store files on the controller
    pusher = observer._share_state(PushFile)
    pusher.args.keep = True
    config_files = {
            entity: send_files_to_controller(pusher, Path(folder), 'opensand_' + entity)
            for folder, entity in args.extra_configuration_folder
    }
    if args.configuration_folder:
        config_files[None] = send_files_to_controller(pusher, args.configuration_folder)

    scenario = opensand_satcom_conf.build(args.satellite, args.gateway, args.terminal, config_files)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
