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


import argparse 
import ipaddress

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.helpers.utils import Validate
from scenario_builder.scenarios import opensand_run


class Entity:
    def __init__(self, entity, opensand_id, emulation_ip, tap_name='opensand_tap'):
        self.entity = entity
        self.opensand_id = int(opensand_id)
        self.emulation_ip = validate_ip(emulation_ip)
        self.tap_name = tap_name


class GatewayPhy:
    def __init__(self, entity_phy, entity_net_acc, interco_phy, interco_net_access):
        self.entity = entity_phy
        self.net_acc_entity = entity_net_acc
        self.interconnect_net_access = validate_ip(interco_net_access)
        self.interconnect_phy = validate_ip(interco_phy)


class Satellite:
    def __init__(self, entity, emulation_ip):
        self.entity = entity
        self.emulation_ip = validate_ip(emulation_ip)


class ValidateSatellite(argparse.Action):
    def __call__(self, parser, args, values, option_string=None): 
        satellite = Satellite(*values)
        setattr(args, self.dest, satellite)


class ValidateTerminal(Validate):
    ENTITY_TYPE = Entity


class ValidateGateway(Validate):
    ENTITY_TYPE = Entity


class ValidateGatewayPhy(Validate):
    ENTITY_TYPE = GatewayPhy


def validate_ip(ip):
    return ipaddress.ip_address(ip).compressed


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--satellite', '--sat', '-s', required=True, action=ValidateSatellite,
            nargs=2, metavar=('ENTITY', 'EMULATION_ADDRESS'),
            help='The satellite of the platform. Must be supplied only once.')
    observer.add_scenario_argument(
            '--gateway', '-gw', required=True, action=ValidateGateway, nargs=4,
            metavar=('ENTITY', 'OPENSAND_ID', 'EMULATION_ADDRESS', 'TAP_NAME'),
            help='A gateway in the platform. Must be supplied at least once.')
    observer.add_scenario_argument(
            '--gateway-phy', '-gwp', required=False, action=ValidateGatewayPhy,
            nargs=4, metavar=('ENTITY_PHY', 'ENTITY_NET_ACC','INTERCONNECT_PHY_ADDRESS', 'INTERCONNECT_NET_ACC_ADDRESS'),
            help='The physical part of a split gateway. Must reference the '
            'net access part previously provided using the --gateway option. '
            'Optional, can be supplied only once per gateway.')
    observer.add_scenario_argument(
            '--satellite-terminal', '-st', required=True, action=ValidateTerminal, nargs=4,
            metavar=('ENTITY', 'OPENSAND_ID', 'EMULATION_ADDRESS', 'TAP_NAME'),
            help='A satellite terminal in the platform. Must be supplied at least once.')
    observer.add_scenario_argument(
            '--duration', '-d', required=False, default=0, type=int,
            help='Duration of the opensand run test, leave blank for endless emulation.')

    args = observer.parse(argv, opensand_run.SCENARIO_NAME)

    run_gateways = []
    phy_gateways = args.gateway_phy or []
    for gateway in args.gateway:
        for gateway_phy in phy_gateways:
            if gateway.entity == gateway_phy.net_acc_entity:
                run_gateways.append(opensand_run.SPLIT_GW(
                        gateway.entity,
                        gateway_phy.entity,
                        gateway.opensand_id,
                        gateway.emulation_ip,
                        gateway_phy.interconnect_phy,
                        gateway_phy.interconnect_net_access,
                        gateway.tap_name))
                break
        else:
            run_gateways.append(opensand_run.GW(
                    gateway.entity,
                    gateway.opensand_id,
                    gateway.emulation_ip,
                    gateway.tap_name))

    scenario = opensand_run.build(
            args.satellite,
            run_gateways,
            args.satellite_terminal,
            args.duration,
            args.scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
