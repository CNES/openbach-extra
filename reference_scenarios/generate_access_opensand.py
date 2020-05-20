#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2020 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

"""This scenario builds and launches the OpenSAND scenario
from /openbach-extra/apis/scenario_builder/scenarios/
"""


import argparse 
import tempfile
import warnings
import functools
import ipaddress
from pathlib import Path
from collections import defaultdict

from auditorium_scripts.push_file import PushFile
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import access_opensand
from scenario_builder.scenarios.access_opensand import SAT, GW, SPLIT_GW, ST  # shortcuts


class Entity:
    def __init__(self, entity, emulation_ip, bridge_to_lan, opensand_id, tap_name='opensand_tap', bridge_name='opensand_br'):
        self.entity = entity
        self.opensand_id = int(opensand_id)
        self.emulation_ip = validate_ip(emulation_ip)
        self.bridge_to_lan = bridge_to_lan
        self.tap_name = tap_name
        self.bridge_name = bridge_name


class GatewayPhy:
    def __init__(self, entity, net_access_entity, interco_phy, interco_net_access):
        self.entity = entity
        self.net_access_entity = net_access_entity
        self.interconnect_net_access = validate_ip(interco_net_access)
        self.interconnect_phy = validate_ip(interco_phy)


class Satellite:
    def __init__(self, entity, ip):
        self.entity = entity
        self.ip = validate_ip(ip)


class ValidateSatellite(argparse.Action):
    def __call__(self, parser, args, values, option_string=None): 
        satellite = Satellite(*values)
        setattr(args, self.dest, satellite)


class _Validate(argparse.Action):
    ENTITY_TYPE = None

    def __call__(self, parser, args, values, option_string=None): 
        if getattr(args, self.dest) == None:
            self.items = []

        try:
            entity = self.ENTITY_TYPE(*values)
        except TypeError as e:
            raise argparse.ArgumentError(self, str(e).split('__init__() ', 1)[-1])
        except ValueError as e:
            raise argparse.ArgumentError(self, e)
        self.items.append(entity)
        setattr(args, self.dest, self.items)


class _ValidateOptional:
    pass


class ValidateGateway(_ValidateOptional, _Validate):
    ENTITY_TYPE = Entity


class ValidateGatewayPhy(_Validate):
    ENTITY_TYPE = GatewayPhy


class ValidateSatelliteTerminal(_ValidateOptional, _Validate):
    ENTITY_TYPE = Entity


def validate_ip(ip):
    return ipaddress.ip_address(ip).compressed


def patch_print_help(parser):
    def decorate(printer):
        @functools.wraps(printer)
        def wrapper(file=None):
            nargs = [action.nargs for action in parser._actions]

            for action in parser._actions:
                if isinstance(action, _ValidateOptional):
                    action.nargs = None
            printer(file)

            for action, narg in zip(parser._actions, nargs):
                action.nargs = narg

        return wrapper

    parser.print_help = decorate(parser.print_help)
    parser.print_usage = decorate(parser.print_usage)


def create_gateways(gateways, gateways_phy):
    for gateway in gateways:
        for gateway_phy in gateways_phy:
            if gateway.entity == gateway_phy.net_access_entity:
                yield SPLIT_GW(
                        gateway.entity, gateway_phy.entity,
                        gateway.opensand_id,
                        gateway.tap_name, gateway.bridge_name,
                        gateway.bridge_to_lan, gateway.emulation_ip,
                        gateway_phy.interconnect_net_access,
                        gateway_phy.interconnect_phy)
                break
        else:
            yield GW(
                    gateway.entity, gateway.opensand_id,
                    gateway.tap_name, gateway.bridge_name,
                    gateway.bridge_to_lan, gateway.emulation_ip)


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--sat', '-s', required=True, action=ValidateSatellite,
            nargs=2, metavar=('ENTITY', 'EMULATION_IP'),
            help='The satellite of the platform. Must be supplied only once.')
    observer.add_scenario_argument(
            '--gateway', '-gw', required=True, action=ValidateGateway, nargs='*',
            metavar='ENTITY EMULATION_IP (BRIDGE_IP | BRIDGE_INTERFACE) OPENSAND_ID [TAP_NAME [BRIDGE_NAME]]',
            help='A gateway in the platform. Must be supplied at least once.')
    observer.add_scenario_argument(
            '--gateway-phy', '-gwp', required=False, action=ValidateGatewayPhy,
            nargs=4, metavar=('ENTITY_PHY', 'ENTITY_NET_ACC', 'INTERCONNECT_PHY', 'INTERCONNECT_NET_ACC'),
            help='The physical part of a split gateway. Must reference the '
            'net access part previously provided using the --gateway option. '
            'Optional, can be supplied only once per gateway.')
    observer.add_scenario_argument(
            '--satellite-terminal', '-st', required=True, action=ValidateSatelliteTerminal, nargs='*',
            metavar='ENTITY EMULATION_IP (BRIDGE_IP | BRIDGE_INTERFACE) OPENSAND_ID [TAP_NAME [BRIDGE_NAME]]',
            help='A satellite terminal in the platform. Must be supplied at least once.')
    observer.add_scenario_argument(
            '--duration', '-d', required=False, default=0, type=int,
            help='Duration of the opensand run test, leave blank for endless emulation.')
    observer.add_scenario_argument(
            '--configuration-folder', '--configuration', '-c',
            required=False, type=Path, metavar='PATH',
            help='Path to a configuration folder that should be '
            'dispatched on agents before the simulation.')

    patch_print_help(observer.parser)
    args = observer.parse(argv, access_opensand.SCENARIO_NAME)

    gateways = list(create_gateways(args.gateway, args.gateway_phy or []))
    terminals = [
            ST(st.entity, st.opensand_id, st.tap_name, st.bridge_name, st.bridge_to_lan, st.emulation_ip)
            for st in args.satellite_terminal
    ]
    satellite = SAT(args.sat.entity, args.sat.ip)
  
    config_files = None
    configuration_folder = args.configuration_folder
    if configuration_folder:
        config_files = [
                p.relative_to(configuration_folder)
                for extension in ('conf', 'txt', 'csv', 'input')
                for p in configuration_folder.rglob('*.' + extension)
        ]

        #Store files on the controller
        pusher = observer._share_state(PushFile)
        pusher.args.keep = True
        for config_file in config_files:
            with configuration_folder.joinpath(config_file).open() as local_file:
                pusher.args.local_file = local_file
                pusher.args.remote_path = config_file.as_posix()
                pusher.execute(False)

    scenario = access_opensand.build(
            satellite, gateways, terminals,
            args.duration, config_files,
            scenario_name=args.scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
