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
  - Run OpenSAND in the satellite, the gateways and the STs for an OpenSAND test
"""
import argparse 
import ipaddress

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.helpers.utils import Validate
from scenario_builder.scenarios import opensand_run


class ValidateSatellite(argparse.Action):
    def __call__(self, parser, args, values, option_string=None): 
        satellite = opensand_run.Satellite(*values)
        setattr(args, self.dest, satellite)


class ValidateGroundEntity(Validate):
    ENTITY_TYPE = opensand_run.GroundEntity


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--satellite', '--sat', '-s', required=True, action=ValidateSatellite,
            nargs=3, metavar=('ENTITY', 'INFRASTRUCTURE_PATH', 'TOPOLOGY_PATH'),
            help='The satellite of the platform. Must be supplied only once.')
    observer.add_scenario_argument(
            '--ground-entity', '--ground', '--entity', '-g', '-e',
            required=True, action=ValidateGroundEntity, nargs=4,
            metavar=('ENTITY', 'INFRASTRUCTURE_PATH', 'TOPOLOGY_PATH', 'PROFILE_PATH'),
            help='A ground entity in the platform. Must be supplied at least once.')
    observer.add_scenario_argument(
            '--duration', '-d', type=int, default=0,
            help='Duration of the opensand run test, leave blank for endless emulation.')

    args = observer.parse(argv, opensand_run.SCENARIO_NAME)

    scenario = opensand_run.build(
            args.satellite,
            args.ground_entity or [],
            args.duration,
            args.scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
