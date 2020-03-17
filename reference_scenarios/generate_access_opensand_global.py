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
import functools
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

from auditorium_scripts.push_file import PushFile
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios.access_opensand_global import SAT, GW, ST, WS, build as build_opensand


@functools.lru_cache(maxsize=1)
class _auto_gateway_id:
    IDS = [0, 6]
    def __init__(self):
        self._ids = iter(self.IDS)

    def __int__(self):
        try:
            return next(self._ids)
        except StopIteration:
            raise ValueError('too much gateways; only allowed ids are {}'.format(self.IDS)) from None


@functools.lru_cache(maxsize=1)
class _auto_terminal_id:
    def __init__(self):
        self._id = -1

    def __int__(self):
        while True:
            self._id += 1
            if self._id not in _auto_gateway_id.IDS:
                return self._id


@functools.lru_cache(maxsize=1)
class _auto_mac_address:
    def __init__(self):
        self._id = 0

    def __str__(self):
        self._id += 1
        return ':'.join(format(s, '02x') for s in self._id.to_bytes(6, 'big'))


class Gateway:
    def __init__(
            self, entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_bridge_ip,
            opensand_id=_auto_gateway_id(), opensand_bridge_mac_address=_auto_mac_address()):
        self.entity = entity
        self.lan_ip = validate_ip(lan_ip)
        self.lan_interface = lan_interface
        self.emu_ip = validate_ip(emu_ip)
        self.emu_interface = emu_interface
        self.opensand_bridge_ip = validate_ip(opensand_bridge_ip)
        self.opensand_bridge_mac_address = str(opensand_bridge_mac_address)
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
    def __init__(
            self, entity, gateway_entity, lan_interface,
            emu_interface, lan_ip, emu_ip, opensand_bridge_ip,
            opensand_id=_auto_terminal_id(),
            opensand_bridge_mac_address=_auto_mac_address()):
        self.entity = entity
        self.gateway_entity = gateway_entity
        self.lan_ip = validate_ip(lan_ip)
        self.lan_interface = lan_interface
        self.emu_ip = validate_ip(emu_ip)
        self.emu_interface = emu_interface
        self.opensand_bridge_ip = validate_ip(opensand_bridge_ip)
        self.opensand_bridge_mac_address = str(opensand_bridge_mac_address)
        self.opensand_id = int(opensand_id)


class Satellite:
    def __init__(self, entity, interface, ip):
        self.entity = entity
        self.ip = validate_ip(ip)
        self.interface = interface


class Spot:
    def __init__(self, spot_id, gateway_entity, *terminals):
        self.spot_id = int(spot_id)
        self.gateway_entity = gateway_entity
        self.terminals = terminals


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
    ENTITY_TYPE = Gateway


class ValidateGatewayPhy(_Validate):
    ENTITY_TYPE = GatewayPhy


class ValidateSatelliteTerminal(_ValidateOptional, _Validate):
    ENTITY_TYPE = SatelliteTerminal


class ValidateWorkStation(_Validate):
    ENTITY_TYPE = WorkStation


class ValidateSpot(_ValidateOptional, _Validate):
    ENTITY_TYPE = Spot


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


def create_topology(satellite, gateways, terminals, spots):
    satellite_ip = extract_ip(satellite.ip)

    configuration = ET.Element('configuration')
    configuration.set('component', 'topology')

    sarp = ET.SubElement(configuration, 'sarp')
    default = ET.SubElement(sarp, 'default')
    default.text = '-1'

    ethernet = ET.SubElement(sarp, 'ethernet')
    for address in ('ff:ff:ff:ff:ff:ff', '33:33:**:**:**:**', '01:00:5E:**:**:**'):
        terminal_eth = ET.SubElement(ethernet, 'terminal_eth')
        terminal_eth.set('mac', address)
        terminal_eth.set('tal_id', '31')

    spot_table_ids = defaultdict(list)
    gw_table_ids = {}
    terminal_entities = {}
    gateway_entities = {}

    for terminal in terminals:
        terminal_id = str(terminal.opensand_id)
        terminal_eth = ET.SubElement(ethernet, 'terminal_eth')
        terminal_eth.set('mac', terminal.opensand_bridge_mac_address)
        terminal_eth.set('tal_id', terminal_id)
        terminal_entities[terminal.entity] = terminal

    for gateway in gateways:
        gateway_id = str(gateway.opensand_id)
        gateway_eth = ET.SubElement(ethernet, 'terminal_eth')
        gateway_eth.set('mac', gateway.opensand_bridge_mac_address)
        gateway_eth.set('tal_id', gateway_id)
        gw_table_ids[gateway_id] = []
        gateway_entities[gateway.entity] = gateway

    sat_carriers = ET.SubElement(configuration, 'sat_carrier')

    base_carrier_id = 0
    for spot in spots:
        spot_id = str(spot.spot_id)
        try:
            gateway = gateway_entities[spot.gateway_entity]
        except KeyError:
            warnings.warn(
                    'Spot {} is linked to unknown Gateway {}; ignoring'
                    .format(spot_id, spot.gateway_entity))
            continue
        else:
            gateway_ip = extract_ip(gateway.emu_ip)
            gateway_id = str(gateway.opensand_id)

        for terminal_entity in spot.terminals:
            try:
                terminal = terminal_entities[terminal_entity]
            except KeyError:
                warnings.warn(
                        'Satellite Terminal {} is linked to Spot {} on '
                        'Gateway {} but not configured otherwise; ignoring'
                        .format(terminal_entity, spot_id, gateway_entity))
            else:
                if terminal.gateway_entity == spot.gateway_entity:
                    terminal_id = str(terminal.opensand_id)
                    gw_table_ids[gateway_id].append(terminal_id)
                    spot_table_ids[spot_id].append(terminal_id)
                else:
                    warnings.warn(
                            'Satellite Terminal {} is linked to Gateway {} '
                            'but configured to listen on Spot {} of Gateway '
                            '{}; ignoring'.format(
                                terminal.entity, terminal.gateway_entity,
                                spot_id, spot.gateway_entity))

        spot_element = ET.SubElement(sat_carriers, 'spot')
        spot_element.set('id', spot_id)
        spot_element.set('gw', gateway_id)
        carriers = ET.SubElement(spot_element, 'carriers')
        carrier = ET.SubElement(carriers, 'carrier')
        carrier.set('id', str(base_carrier_id))
        carrier.set('type', 'ctrl_out')
        carrier.set('ip_address', spot.control_multicast_address)
        carrier.set('port', str(spot.control_out_port))
        carrier.set('ip_multicast', 'true')
        base_carrier_id += 1
        carrier = ET.SubElement(carriers, 'carrier')
        carrier.set('id', str(base_carrier_id))
        carrier.set('type', 'ctrl_in')
        carrier.set('ip_address', satellite_ip)
        carrier.set('port', str(spot.control_in_port))
        carrier.set('ip_multicast', 'false')
        base_carrier_id += 1
        carrier = ET.SubElement(carriers, 'carrier')
        carrier.set('id', str(base_carrier_id))
        carrier.set('type', 'logon_out')
        carrier.set('ip_address', gateway_ip)
        carrier.set('port', str(spot.logon_out_port))
        carrier.set('ip_multicast', 'false')
        base_carrier_id += 1
        carrier = ET.SubElement(carriers, 'carrier')
        carrier.set('id', str(base_carrier_id))
        carrier.set('type', 'logon_in')
        carrier.set('ip_address', satellite_ip)
        carrier.set('port', str(spot.logon_in_port))
        carrier.set('ip_multicast', 'false')
        base_carrier_id += 1
        carrier = ET.SubElement(carriers, 'carrier')
        carrier.set('id', str(base_carrier_id))
        carrier.set('type', 'data_out_st')
        carrier.set('ip_address', spot.data_multicast_address)
        carrier.set('port', str(spot.data_out_st_port))
        carrier.set('ip_multicast', 'true')
        base_carrier_id += 1
        carrier = ET.SubElement(carriers, 'carrier')
        carrier.set('id', str(base_carrier_id))
        carrier.set('type', 'data_in_st')
        carrier.set('ip_address', satellite_ip)
        carrier.set('port', str(spot.data_in_st_port))
        carrier.set('ip_multicast', 'false')
        base_carrier_id += 1
        carrier = ET.SubElement(carriers, 'carrier')
        carrier.set('id', str(base_carrier_id))
        carrier.set('type', 'data_out_gw')
        carrier.set('ip_address', gateway_ip)
        carrier.set('port', str(spot.data_out_gw_port))
        carrier.set('ip_multicast', 'false')
        base_carrier_id += 1
        carrier = ET.SubElement(carriers, 'carrier')
        carrier.set('id', str(base_carrier_id))
        carrier.set('type', 'data_in_gw')
        carrier.set('ip_address', satellite_ip)
        carrier.set('port', str(spot.data_in_gw_port))
        carrier.set('ip_multicast', 'false')
        base_carrier_id += 1

    spot_table = ET.SubElement(configuration, 'spot_table')
    for spot_id, spot_terminals in spot_table_ids.items():
        spot = ET.SubElement(spot_table, 'spot')
        spot.set('id', spot_id)
        terminals = ET.SubElement(spot, 'terminals')
        for terminal_id in spot_terminals:
            terminal = ET.SubElement(terminals, 'tal')
            terminal.set('id', terminal_id)
    default = ET.SubElement(spot_table, 'default_spot')
    default.text = '1'

    gw_table = ET.SubElement(configuration, 'gw_table')
    for gateway_id, gateway_terminals in gw_table_ids.items():
        gw = ET.SubElement(gw_table, 'gw')
        gw.set('id', gateway_id)
        terminals = ET.SubElement(gw, 'terminals')
        for terminal_id in gateway_terminals:
            terminal = ET.SubElement(terminals, 'tal')
            terminal.set('id', terminal_id)
    default = ET.SubElement(gw_table, 'default_spot')
    default.text = '0'

    return ET.ElementTree(configuration)


def indent_xml(element, padding='\t', level=0, last=True):
    """Indent an xml.etree.ElementTree.Element tree for pretty printing"""
    if element:
        next_level = level + 1
        if not element.text or not element.text.strip():
            element.text = '\n' + padding * next_level
        for idx, sub_element in enumerate(reversed(element)):
            indent_xml(sub_element, padding, next_level, not idx)
    if not element.tail or not element.tail.strip():
        element.tail = '\n' + padding * (level - last)


def create_network(satellite_ip, satellite_subnet_mask, gateways, gateways_phy, terminals, workstations):
    satellite_subnet = '{}/{}'.format(extract_ip(satellite_ip), satellite_subnet_mask)
    host_route_ip = extract_network(satellite_subnet)

    opensand_ids = set()
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

        if gateway.opensand_id in opensand_ids:
            warnings.warn('Gateway {} uses an ID already used by another entity'.format(gateway.entity))
        opensand_ids.add(gateway.opensand_id)

        found = False
        for workstation in workstations:
            if workstation.opensand_entity == gateway.entity:
                if found:
                    warnings.warn('More than one server workstation configured for gateway {}'.format(gateway.entity))
                work_stations.append(WS(
                    workstation.entity,
                    workstation.interface,
                    workstation.ip,
                    host_route_ip,
                    extract_ip(gateway.lan_ip)))
                found = True

        if not found:
            warnings.warn('No server workstation configured for gateway {}'.format(gateway.entity))

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

                if terminal.opensand_id in opensand_ids:
                    warnings.warn('Terminal {} uses an ID already used by another entity'.format(terminal.entity))
                opensand_ids.add(terminal.opensand_id)

                found = False
                for workstation in workstations:
                    if workstation.opensand_entity == terminal.entity:
                        if found:
                            warnings.warn('More than one client workstation configured for terminal {}'.format(terminal.entity))
                        work_stations.append(WS(
                            workstation.entity,
                            workstation.interface,
                            workstation.ip,
                            host_route_ip,
                            extract_ip(terminal.lan_ip)))
                        found = True

                if not found:
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
                    terminal.opensand_bridge_mac_address,
                    terminal.opensand_id)
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
            gateway.opensand_id,
            gw_terminals,
            gateway_phy_entity,
            gateway_phy_interfaces,
            gateway_phy_ips))

    return opensand_gateways, work_stations


def main(scenario_name='access_opensand', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--sat', '-s', required=True, action=ValidateSatellite, nargs=3,
            metavar=('ENTITY', 'EMU_INTERFACE', 'EMU_IP'),
            help='The satellite of the platform. Must be supplied only once.')
    observer.add_scenario_argument(
            '--gateway', '-gw', required=True, action=ValidateGateway, nargs='*',
            help='A gateway in the platform. Must be supplied at least once.',
            metavar='ENTITY LAN_INTERFACE EMU_INTERFACE LAN_IP EMU_IP OPENSAND_BRIDGE_IP '
            '[OPENSAND_ID [OPENSAND_BRIDGE_MAC_ADDRESS]]')
    observer.add_scenario_argument(
            '--gateway-phy', '-gwp', required=False, action=ValidateGatewayPhy, nargs=6,
            help='The physical part of a split gateway. Must reference the '
            'net access part previously provided using the --gateway option. '
            'Optional, can be supplied only once per gateway.',
            metavar=('ENTITY', 'NET_ACCESS_ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP','EMU_IP'))
    observer.add_scenario_argument(
            '--satellite-terminal', '-st', required=True, action=ValidateSatelliteTerminal, nargs='*',
            help='A satellite terminal in the platform. Must be supplied at '
            'least once and reference the gateway it is attached to.',
            metavar='ENTITY GATEWAY_ENTITY LAN_INTERFACE EMU_INTERFACE LAN_IP EMU_IP '
            'OPENSAND_BRIDGE_IP [OPENSAND_ID [OPENSAND_BRIDGE_MAC_ADDRESS]]')
    observer.add_scenario_argument(
            '--spot', required=False, action=ValidateSpot, nargs='*',
            help='A spot associated to a gateway and serving several '
            'terminals. Presence of spots is optional but will override any '
            'topology.conf found using the --configuration-folder option.',
            metavar='SPOT_ID GATEWAY_ENTITY [TERMINAL_ENTITY [TERMINAL_ENTITY [...]]]')
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
            'agents before the simulation. If --spot are defined, a topology.conf '
            'file will be generated and added to the files found in this folder.')

    patch_print_help(observer.parser)
    args = observer.parse(argv, scenario_name)

    if args.spot:
        topology = create_topology(args.sat, args.gateway, args.satellite_terminal, args.spot)
        indent_xml(topology.getroot())

    gateways, workstations = create_network(
        args.sat.ip, 16,
        args.gateway,
        args.gateway_phy or [],
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

        if args.spot:
            with tempfile.NamedTemporaryFile() as topology_conf:
                topology.write(topology_conf, 'UTF-8', True)
                topology_conf.seek(0)
                pusher.args.local_file = topology_conf
                pusher.args.remote_path = 'topology.conf'
                pusher.execute(False)
            if Path("topology.conf") not in config_files:
                config_files.append(Path("topology.conf"))

    scenario = build_opensand(
            SAT(satellite.entity, satellite.interface, satellite.ip),
            gateways, workstations,
            args.duration, config_files)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
