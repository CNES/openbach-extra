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
import ipaddress
from pathlib import Path
from collections import namedtuple

from auditorium_scripts.push_file import PushFile
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios.access_opensand import GW, ST, WS, build as build_opensand


class Gateway:
    def __init__(self, entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_bridge_ip, opensand_bridge_mac_address, opensand_id):
        self.entity = entity
        self.lan_ip = validate_ip(lan_ip)
        self.lan_interface = lan_interface
        self.emu_ip = validate_ip(emu_ip)
        self.emu_interface = emu_interface
        self.opensand_bridge_ip = validate_ip(opensand_bridge_ip)
        self.opensand_bridge_mac_address = opensand_bridge_mac_address
        self.opensand_id = int(opensand_id)


class GatewayPhy:
    def __init__(self, entity, net_access_entity, lan_interface, emu_interface, lan_ip, emu_ip):
        self.entity = entity
        self.lan_ip = validate_ip(lan_ip)
        self.lan_interface = lan_interface
        self.emu_ip = validate_ip(emu_ip)
        self.emu_interface = emu_interface
        self.net_access_entity = net_access_entity


class SatelliteTerminal:
    def __init__(self, entity, gateway_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_bridge_ip, opensand_bridge_mac_address, opensand_id):
        self.entity = entity
        self.gateway_entity = gateway_entity
        self.lan_ip = validate_ip(lan_ip)
        self.lan_interface = lan_interface
        self.emu_ip = validate_ip(emu_ip)
        self.emu_interface = emu_interface
        self.opensand_bridge_ip = validate_ip(opensand_bridge_ip)
        self.opensand_bridge_mac_address = opensand_bridge_mac_address
        self.opensand_id = int(opensand_id)


class Satellite:
    def __init__(self, entity, interface, ip):
        self.entity = entity
        self.ip = validate_ip(ip)
        self.interface = interface


class WorkStation:
    def __init__(self, entity, opensand_entity, interface, ip):
        self.entity = entity
        self.ip = validate_ip(ip)
        self.interface = interface
        self.opensand_entity = opensand_entity
        

class ValidateSatellite(argparse.Action):
    def __call__(self, parser, args, values, option_string=None): 
        satellite = Satellite(*values)
        setattr(args, self.dest, satellite)


class _Validate(argparse.Action):
    ENTITY_TYPE = None

    def __call__(self, parser, args, values, option_string=None): 
        if getattr(args, self.dest) == None:
            self.items = []

        entity = self.ENTITY_TYPE(*values)
        self.items.append(entity)
        setattr(args, self.dest, self.items)


class ValidateGateway(_Validate):
    ENTITY_TYPE = Gateway


class ValidateGatewayPhy(_Validate):
    ENTITY_TYPE = GatewayPhy


class ValidateSatelliteTerminal(_Validate):
    ENTITY_TYPE = SatelliteTerminal


class ValidateWorkStation(_Validate):
    ENTITY_TYPE = WorkStation


def validate_ip(ip):
    return ipaddress.ip_interface(ip).with_prefixlen


def extract_network(ip):
    return ipaddress.ip_interface(ip).network.with_prefixlen


def extract_ip(ip):
    return ipaddress.ip_interface(ip).ip.compressed


def find_routes(routes, ip):
    network = extract_network(ip)
    return [
            route
            for route in routes
            if ipaddress.ip_network(route) != ipaddress.ip_network(network)
    ]


def create_network(satellite_ip, satellite_subnet_mask, gateways, gateways_phy, terminals, workstations):
    satellite_subnet = '{}/{}'.format(extract_ip(satellite_ip), satellite_subnet_mask)
    host_route_ip = extract_network(satellite_subnet)

    work_stations = []
    opensand_gateways = []

    for gateway in gateways:

        route_ips = [extract_network(gateway.lan_ip)]
        route_gateway_ip = extract_ip(gateway.opensand_bridge_ip)
        opensand_terminals = []
        terminal_ips = []
        gateway_phy_entity = None
        gateway_phy_interfaces = []
        gateway_phy_ips = []

        server = False
        for workstation in workstations:
            if workstation.opensand_entity == gateway.entity:
                if server:
                    warnings.warn('More than one server workstation configured for gateway {}'.format(gateway.entity))
                work_stations.append(WS(
                    workstation.entity,
                    workstation.interface,
                    workstation.ip,
                    host_route_ip,
                    extract_ip(gateway.lan_ip)))
                server = True

        if not server:
            warning.warn('No server workstation configured for gateway {}'.format(gateway.entity))

        if gateways_phy:
            for gateway_phy in gateways_phy:
                if gateway_phy.net_access_entity == gateway.entity:
                    if gateway_phy_entity is not None:
                        warnings.warn('More than one gateway_phy configured for the gateway_net_acc {}, keeping only the last one'.format(gateway.entity))
                    gateway_phy_entity = gateway_phy.entity
                    gateway_phy_interfaces = [gateway_phy.lan_interface, gateway_phy.emu_interface]
                    gateway_phy_ips = [gateway_phy.lan_ip, gateway_phy.emu_ip]

        for terminal in terminals:
            if terminal.gateway_entity == gateway.entity:
                route_ips.append(extract_network(terminal.lan_ip))
                terminal_ips.append(extract_ip(terminal.opensand_bridge_ip))
                opensand_terminals.append(terminal)

                client = False
                for workstation in workstations:
                    if workstation.opensand_entity == terminal.entity:
                        if client:
                            warnings.warn('More than one client workstation configured for terminal {}'.format(terminal.entity))
                        work_stations.append(WS(
                            workstation.entity,
                            workstation.interface,
                            workstation.ip,
                            host_route_ip,
                            extract_ip(terminal.lan_ip)))
                        client = True

                if not client:
                    warnings.warn('No client workstation configured for terminal {}'.format(terminal.entity))

        if not opensand_terminals:
            warnings.warn('Gateway {} does not have any associated terminal'.format(gateway.entity))

        gw_terminals = [
                ST(
                    terminal.entity,
                    [terminal.lan_interface, terminal.emu_interface],
                    [terminal.lan_ip, terminal.emu_ip],
                    find_routes(route_ips, terminal.lan_ip),
                    route_gateway_ip,
                    terminal.opensand_bridge_ip,
                    terminal.opensand_bridge_mac_address)
                for terminal in opensand_terminals
        ]
        
        opensand_gateways.append(GW(
            gateway.entity,
            [gateway.lan_interface, gateway.emu_interface],
            [gateway.lan_ip, gateway.emu_ip],
            find_routes(route_ips, gateway.lan_ip),
            terminal_ips,
            gateway.opensand_bridge_ip,
            gateway.opensand_bridge_mac_address,
            gw_terminals,
            gateway_phy_entity,
            gateway_phy_interfaces,
            gateway_phy_ips))

    return opensand_gateways, work_stations


def main(scenario_name='opensand', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--sat', '-s', required=True, action=ValidateSatellite, nargs=3,
            metavar=('ENTITY', 'EMU_INTERFACE', 'EMU_IP'),
            help='The satellite of the platform. Must be supplied only once.')
    observer.add_scenario_argument(
            '--gateway', '-gw', required=True, action=ValidateGateway, nargs=8,
            help='A gateway in the platform. Must be supplied at least once.',
            metavar=('ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP','EMU_IP', 
                     'OPENSAND_BRIDGE_IP', 'OPENSAND_BRIDGE_MAC_ADDRESS', 'OPENSAND_ID'))
    observer.add_scenario_argument(
            '--gateway-phy', '-gwp', required=False, action=ValidateGatewayPhy, nargs=6,
            help='The physical part of a split gateway. Must reference the '
            'net access part previously provided using the --gateway option. '
            'Optional, can be supplied only once per gateway.',
            metavar=('ENTITY', 'NET_ACCESS_ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP','EMU_IP'))
    observer.add_scenario_argument(
            '--satellite-terminal', '-st', required=True, action=ValidateSatelliteTerminal, nargs=9,
            help='A satellite terminal in the platform. Must be supplied at '
            'least once and reference the gateway it is attached to.',
            metavar=(
                'ENTITY', 'GATEWAY_ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP', 'EMU_IP',
                'OPENSAND_BRIDGE_IP', 'OPENSAND_BRIDGE_MAC_ADDRESS', 'OPENSAND_ID'))
    observer.add_scenario_argument(
            '--workstation', '-ws', required=False, action=ValidateWorkStation, nargs=4,
            help='A workstation to configure alongside the main OpenSAND platform. '
            'Must reference an existing gateway or satellite terminal. Optional, '
            'can be supplied several times per OpenSAND entity.',
            metavar=('ENTITY', 'OPENSAND_ENTITY', 'LAN_INTERFACE', 'LAN_IP'))
    observer.add_scenario_argument(
            '--duration', '-d', required=False, default=0, type=int,
            help='Duration of the opensand run test, leave blank for endless emulation.')
    observer.add_scenario_argument(
            '--configuration-folder', '--configuration', '-c',
            required=False, type=Path, metavar='PATH',
            help='Path to a configuration folder that should be dispatched on '
            'agents before the simulation.')

    args = observer.parse(argv, scenario_name)
    gateways, workstations = create_network(
        args.sat.ip, 16,
        args.gateway,
        args.gateway_phy,
        args.satellite_terminal,
        args.workstation or [])
    satellite = args.sat
  
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

    scenario = build_opensand(
            satellite.entity, satellite.interface, satellite.ip,
            gateways, workstations,
            args.duration, config_files)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
