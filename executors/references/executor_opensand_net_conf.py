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
 - Configure bridge/tap interfaces on entities for OpenSAND to communicate with the real world
 - Configure ip forwarding in case IP mode is requested
 - Clear the configuration if requested
 This step is necessary to set up an OpenSAND platform.
"""

import argparse 
from dataclasses import dataclass

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.helpers.utils import Validate, ValidateOptional, patch_print_help
from scenario_builder.scenarios import opensand_net_conf


@dataclass(frozen=True)
class Entity:
    name: str
    bridge_to_lan: str
    tap_name: str = 'opensand_tap'
    bridge_name: str = 'opensand_br'
    tap_mac: str = None


class ValidateEntity(ValidateOptional, Validate):
    ENTITY_TYPE = Entity


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--clear', '-c', action='store_true',
            help='Clear the network configuration on the provided entities instead of applying it.')
    observer.add_scenario_argument(
            '--entity', '-e', action=ValidateEntity, nargs='*',
            metavar='ENTITY (BRIDGE_ADDRESS_MASK | BRIDGE_INTERFACE) [TAP_NAME [BRIDGE_NAME [TAP_MAC]]]',
            help='A simulated entity in the network. Can be specified several times.')

    patch_print_help(observer.parser)
    args = observer.parse(argv, opensand_net_conf.SCENARIO_NAME)

    mode = 'delete' if args.clear else 'configure'
    scenario = opensand_net_conf.build(args.entity, mode, args.scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
