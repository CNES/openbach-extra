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


import time
import argparse 
import tempfile
from pathlib import Path

from auditorium_scripts.push_file import PushFile
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.helpers.utils import Validate
from scenario_builder.scenarios import opensand_satcom_conf


class ValidateSatellite(argparse.Action):
    def __call__(self, parser, args, values, option_string=None): 
        satellite = opensand_satcom_conf.SAT(*values)
        setattr(args, self.dest, satellite)


class ValidateGroundEntity(Validate):
    ENTITY_TYPE = opensand_satcom_conf.GROUND


def send_files_to_controller(pusher, entity, prefix='opensand'):
    name, *files = entity
    destination = Path(prefix, name)

    for config_file in map(Path, files):
        with config_file.open() as local_file:
            pusher.args.local_file = local_file
            pusher.args.remote_path = (destination / config_file.name).as_posix()
            pusher.execute(False)
        # If we don't use this, the controller has a tendency to close the
        # connection after some files, so slowing things down the dirty way.
        time.sleep(0.1)

    return entity.__class__(name, *(Path(f).name for f in files))


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--satellite', '--sat', '-s',
            required=True, action=ValidateSatellite, nargs=3,
            metavar=('ENTITY', 'INFRASTRUCTURE_PATH', 'TOPOLOGY_PATH'),
            help='The entity running the satellite of the platform.')
    observer.add_scenario_argument(
            '--ground-entity', '--ground', '--entity', '-g', '-e',
            action=ValidateGroundEntity, nargs=4,
            metavar=('ENTITY', 'INFRASTRUCTURE_PATH', 'TOPOLOGY_PATH', 'PROFILE_PATH'),
            help='The entity running a ground entity in the platform. Can be supplied several times.')

    args = observer.parse(argv, opensand_satcom_conf.SCENARIO_NAME)

    #Store files on the controller
    pusher = observer.share_state(PushFile)
    pusher.args.keep = True
    satellite = send_files_to_controller(pusher, args.satellite)
    ground = [
            send_files_to_controller(pusher, ground_entity)
            for ground_entity in args.ground_entity
    ]

    scenario = opensand_satcom_conf.build(satellite, ground)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
