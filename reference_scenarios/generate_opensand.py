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
from collections import namedtuple
from pathlib import Path
import pprint
from auditorium_scripts.scenario_observer import ScenarioObserver
from auditorium_scripts.push_file import PushFile
from scenario_builder.scenarios import opensand


class Gateway:
    def __init__(self, entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip):
        self.entity = entity
        self.lan_ip = validate_ip(lan_ip)
        self.lan_interface = lan_interface
        self.emu_ip = validate_ip(emu_ip)
        self.emu_interface = emu_interface
        self.opensand_ip = validate_ip(opensand_ip)



class GatewayPhy:
    def __init__(self, entity, lan_interface, emu_interface, lan_ip, emu_ip, net_access_entity):
        self.entity = entity
        self.lan_ip = validate_ip(lan_ip)
        self.lan_interface = lan_interface
        self.emu_ip = validate_ip(emu_ip)
        self.emu_interface = emu_interface
        self.net_access_entity = net_access_entity


class SatelliteTerminal:
    def __init__(self, entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip, gateway_entity):
        self.entity = entity
        self.lan_ip = validate_ip(lan_ip)
        self.lan_interface = lan_interface
        self.emu_ip = validate_ip(emu_ip)
        self.emu_interface = emu_interface
        self.opensand_ip = validate_ip(opensand_ip)
        self.gateway_entity = gateway_entity


class Satellite:
    def __init__(self, entity, interface, ip):
        self.entity = entity
        self.ip = validate_ip(ip)
        self.interface = interface


class WorkStation:
    def __init__(self, entity, interface, ip, opensand_entity):
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


def create_network(satellite_ip, satellite_subnet_mask, gateways, gateways_φ, terminals, workstations):
    satellite_subnet = '{}/{}'.format(extract_ip(satellite_ip), satellite_subnet_mask)
    host_route_ip = extract_network(satellite_subnet)

    work_stations = []
    opensand_gateways = []

    for gateway in gateways:

        route_ips = [extract_network(gateway.lan_ip)]
        route_gateway_ip = extract_ip(gateway.opensand_ip)
        opensand_terminals = []
        terminal_ips = []
        gatewayφ_entity = None
        gatewayφ_interfaces = []
        gatewayφ_ips = []

        server = False
        for workstation in workstations:
            if workstation.opensand_entity == gateway.entity:
                if server:
                    warnings.warn('More than one server workstation configured for gateway {}'.format(gateway.entity))
                work_stations.append(opensand.WS(
                    workstation.entity,
                    workstation.interface,
                    workstation.ip,
                    host_route_ip,
                    extract_ip(gateway.lan_ip)))
                server = True

        if not server:
            warning.warn('No server workstation configured for gateway {}'.format(gateway.entity))

        if gateways_φ:
            for gatewayφ in gateways_φ:
                if gatewayφ.net_access_entity == gateway.entity:
                    if gatewayφ_entity is not None:
                        warnings.warn('More than one gateway_phy configured for the gateway_net_acc {}, keeping only the last one'.format(gateway.entity))
                    gatewayφ_entity = gatewayφ.entity
                    gatewayφ_interfaces = [gatewayφ.lan_interface, gatewayφ.emu_interface]
                    gatewayφ_ips = [gatewayφ.lan_ip, gatewayφ.emu_ip]

        for terminal in terminals:
            if terminal.gateway_entity == gateway.entity:
                route_ips.append(extract_network(terminal.lan_ip))
                terminal_ips.append(extract_ip(terminal.opensand_ip))
                opensand_terminals.append(terminal)

                client = False
                for workstation in workstations:
                    if workstation.opensand_entity == terminal.entity:
                        if client:
                            warnings.warn('More than one client workstation configured for terminal {}'.format(terminal.entity))
                        work_stations.append(opensand.WS(
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
                opensand.ST(
                    terminal.entity,
                    [terminal.lan_interface, terminal.emu_interface],
                    [terminal.lan_ip, terminal.emu_ip],
                    find_routes(route_ips, terminal.lan_ip),
                    route_gateway_ip,
                    terminal.opensand_ip)
                for terminal in opensand_terminals
        ]
        
        opensand_gateways.append(opensand.GW(
            gateway.entity,
            [gateway.lan_interface, gateway.emu_interface],
            [gateway.lan_ip, gateway.emu_ip],
            find_routes(route_ips, gateway.lan_ip),
            terminal_ips,
            gateway.opensand_ip,
            gw_terminals,
            gatewayφ_entity,
            gatewayφ_interfaces,
            gatewayφ_ips))

    return opensand_gateways, work_stations


def main(scenario_name='opensand', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--sat', '-s', required=True, action=ValidateSatellite, nargs=3,
            metavar=('SAT_ENTITY', 'SAT_INTERFACE', 'SAT_IP'),
            help='Info for the satellite : sat_entity, sat_interface and sat_ip')
    observer.add_scenario_argument(
            '--gateway', '-gw', required=True, action=ValidateGateway, nargs=6,
            help='Info for GW: gw_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip',
            metavar=('GW_ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP','EMU_IP', 'OPENSAND_IP'))
    observer.add_scenario_argument(
            '--gateway-phy', '-gwp', required=False, action=ValidateGatewayPhy, nargs=6,
            help='Info for GW_PHY: gw_phy_entity, lan_interface, emu_interface, lan_ip, emu_ip, gw_entity',
            metavar=('GW_PHY_ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP','EMU_IP', 'GW_ENTITY'))
    observer.add_scenario_argument(
            '--satellite-terminal', '-st', required=True, action=ValidateSatelliteTerminal, nargs=7,
            help='Info for ST: st_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip, gw_entity', 
            metavar=('ST_ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP', 'EMU_IP', 'OPENSAND_IP', 'GW_ENTITY'))
    observer.add_scenario_argument(
            '--workstation', '-ws', required=False, action=ValidateWorkStation, nargs=4,
            help='Info for WS: ws_entity, interface, interface, lan_ip, opensand_entity',
            metavar=('WS_ENTITY', 'INTERFACE', 'IP', 'OPENSAND_ENTITY'))
    observer.add_scenario_argument(
            '--duration', '-d', required=False, default=0, type=int,
            help='Duration of the opensand run test, default = 0 (no end)')
    observer.add_scenario_argument(
            '--pushfile', '-pf', required=False, default='', type=str,
            help='Path to config files')

    args = observer.parse(argv, scenario_name)
    gateways, workstations = create_network(
        args.sat.ip, 16,
        args.gateway,
        args.gateway_phy,
        args.satellite_terminal,
        args.workstation)
    satellite = args.sat
  
    stored_file = []
    pushfile = args.pushfile
    if pushfile != '':
        path_conf_file = sorted(Path(args.pushfile).rglob('*.conf'))

        pusher = observer._share_state(PushFile)
        pusher.args.keep = True
        #Store files on the controller
        for local_file in path_conf_file:
            localfile = open(str(local_file), 'r')
            pusher.args.local_file = localfile
            pusher.args.remote_path = 'opensand/' + str(local_file).split(pushfile)[-1]
            pusher.execute(True)
            stored_file.append('opensand/' + str(local_file).split(pushfile)[-1])
            localfile.close()
        
    scenario = opensand.build(satellite.entity, satellite.interface, satellite.ip, gateways, workstations, args.duration, stored_file)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
