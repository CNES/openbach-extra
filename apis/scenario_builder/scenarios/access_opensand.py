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

import ipaddress
import itertools
from collections import namedtuple

from scenario_builder import Scenario
from scenario_builder.helpers.access import opensand
from scenario_builder.helpers.admin.push_file import push_file


CONFIGURE_DESCRIPTION = """This configure opensand system scenario allows to:
 - Configure the satellite, the gateways, the ST, the SRV and the CLT for an opensand test
"""
CONFIGURE_NAME = 'access_opensand_configure'

RUN_DESCRIPTION = """This run opensand scenario allows to:
 - Run opensand in the satellite, the gateways and the STs for an opensand test
"""
RUN_NAME = 'access_opensand_run'

CLEAR_DESCRIPTION = """This clear simple system scenario allows to:
 - Clear the satellite, the gateways, the ST, the SRV and the CLT from an opensand test
"""
CLEAR_NAME = 'access_opensand_clear'

PUSH_DESCRIPTION = """This push file scenario allows to:
 - Push conf files to the satellite, the gateways, and the ST from the controller
"""
PUSH_NAME = 'access_opensand_push'

SCENARIO_DESCRIPTION = """This is reference OpenSAND scenario"""
SCENARIO_NAME = 'access_opensand'


WS = namedtuple('WS', ('entity', 'interfaces', 'ips', 'route_ips', 'gateway_route'))
ST = namedtuple('ST', WS._fields + ('opensand_bridge_ip', 'opensand_bridge_mac_address', 'opensand_id'))
class GW(ST):
    def __new__(
            self, entity, interfaces, ips, route_ips, terminals_ips,
            opensand_bridge_ip, opensand_bridge_mac_address, opensand_id, terminals,
            gateway_phy_entity=None, gateway_phy_interface=None, gateway_phy_ip=None):
        return super().__new__(
                self, entity, interfaces, ips, route_ips, terminals_ips,
                opensand_bridge_ip, opensand_bridge_mac_address, opensand_id)
    def __init__(
            self, entity, interfaces, ips, route_ips, terminals_routes,
            opensand_bridge_ip, opensand_bridge_mac_address, opensand_id, terminals,
            gateway_phy_entity=None, gateway_phy_interfaces=None, gateway_phy_ips=None):
        self.terminals = terminals
        self.gateway_phy_entity = None
        if gateway_phy_entity is not None:
            self.gateway_phy_entity = gateway_phy_entity
            self.gateway_phy_ips = gateway_phy_ips
            self.gateway_phy_interfaces = gateway_phy_interfaces


def configure(satellite_entity, satellite_interface, satellite_ip, gateways, work_stations=(), scenario_name=CONFIGURE_NAME):
    scenario = Scenario(scenario_name, CONFIGURE_DESCRIPTION)
    opensand.configure_satellite(scenario, satellite_entity, satellite_interface, satellite_ip)

    for gateway in gateways:
        opensand.configure_gateway(
                scenario, gateway.entity,
                gateway.interfaces, gateway.ips, gateway.opensand_bridge_ip,
                gateway.route_ips, gateway.gateway_route, gateway.opensand_bridge_mac_address)
        if gateway.gateway_phy_entity is not None:
            opensand.configure_gateway_phy(
                    scenario, gateway.gateway_phy_entity,
                    gateway.gateway_phy_interfaces, gateway.gateway_phy_ips)

        for terminal in gateway.terminals:
            opensand.configure_terminal(
                    scenario, terminal.entity,
                    terminal.interfaces, terminal.ips, terminal.opensand_bridge_ip,
                    terminal.route_ips, terminal.gateway_route, terminal.opensand_bridge_mac_address)

    for host in work_stations:
        opensand.configure_workstation(
                scenario, host.entity,
                host.interfaces, host.ips,
                host.route_ips, host.gateway_route)

    return scenario


def _extract_ip(ip_with_mask):
    return ipaddress.ip_interface(ip_with_mask).ip.compressed


def run(satellite_entity, satellite_ip, gateways, scenario_name=RUN_NAME):
    scenario = Scenario(scenario_name, RUN_DESCRIPTION)
    opensand.opensand_run(scenario, satellite_entity, 'sat', emulation_address=_extract_ip(satellite_ip))

    for gateway in gateways:
        _, emulation_address = map(_extract_ip, gateway.ips)

        if gateway.gateway_phy_entity is not None:
            opensand.opensand_run(
                    scenario, gateway.entity, 'gw-net-acc',
                    entity_id=gateway.opensand_id,
                    interconnection_address=emulation_address)
            interconnect_address, emulation_address = map(_extract_ip, gateway.gateway_phy_ips)
            opensand.opensand_run(
                    scenario, gateway.gateway_phy_entity, 'gw-phy',
                    entity_id=gateway.opensand_id,
                    emulation_address=emulation_address,
                    interconnection_address=interconnect_address)
        else:
            opensand.opensand_run(
                    scenario, gateway.entity, 'gw',
                    entity_id=gateway.opensand_id,
                    emulation_address=emulation_address)

        for terminal in gateway.terminals:
            _, emulation_address = map(_extract_ip, terminal.ips)
            opensand.opensand_run(
                    scenario, terminal.entity, 'st',
                    entity_id=terminal.opensand_id,
                    emulation_address=emulation_address)

    return scenario


def clear(satellite_entity, satellite_interface, gateways, work_stations=(), scenario_name=CLEAR_NAME):
    scenario = Scenario(scenario_name, CLEAR_DESCRIPTION)
    opensand.clear_satellite(scenario, satellite_entity, satellite_interface)

    for gateway in gateways:
        opensand.clear_gateway(
                scenario, gateway.entity,
                gateway.interfaces)
        if gateway.gateway_phy_entity is not None:
            opensand.clear_gateway_phy(
                    scenario, gateway.gateway_phy_entity,
                    gateway.gateway_phy_interfaces)

        for terminal in gateway.terminals:
            opensand.clear_terminal(
                    scenario, terminal.entity,
                    terminal.interfaces)

    for host in work_stations:
        opensand.clear_workstation(
                scenario, host.entity,
                host.interfaces)

    return scenario


def _build_remote_and_users(configuration_per_entity, entity_name, prefix='/etc/opensand/'):
    common_files = configuration_per_entity[None]
    entity_files = configuration_per_entity[entity_name]
    local_files = [f.as_posix() for f in itertools.chain(common_files, entity_files)]
    remote_files = [(prefix / f).as_posix() for f in common_files]
    remote_files.extend((prefix / f.relative_to(entity_name)).as_posix() for f in entity_files)
    users = ['opensand'] * len(local_files)
    groups = ['root'] * len(local_files)
    return remote_files, local_files, users, groups


def push_conf(satellite_entity, gateways, configuration_files, scenario_name=PUSH_NAME):
    configuration_per_entity = {
            'sat': [],
            'st': [],
            'gw': [],
            None: [],
    }
    for config_file in configuration_files:
        entity = config_file.parts[0]
        if entity not in configuration_per_entity:
            entity = None
        configuration_per_entity[entity].append(config_file)

    scenario = Scenario(scenario_name, PUSH_DESCRIPTION)

    push_file(scenario, satellite_entity, *_build_remote_and_users(configuration_per_entity, 'sat'))
    for gateway in gateways:
        files = _build_remote_and_users(configuration_per_entity, 'gw')
        push_file(scenario, gateway.entity, *files)
        if gateway.gateway_phy_entity:
            push_file(scenario, gateway.gateway_phy_entity, *files)

        files = _build_remote_and_users(configuration_per_entity, 'st')
        for terminal in gateway.terminals:
            push_file(scenario, terminal.entity, *files)

    return scenario


def build(satellite_entity, satellite_interface, satellite_ip, gateways, workstations=(), duration=0, configuration_files=None, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    scenario_configure = configure(satellite_entity, satellite_interface, satellite_ip, gateways, workstations)
    start_scenario_configure = scenario.add_function('start_scenario_instance')
    start_scenario_configure.configure(scenario_configure)
    wait = [start_scenario_configure]
 
    if configuration_files:
        scenario_push = push_conf(satellite_entity, gateways, configuration_files)
        start_scenario_push = scenario.add_function('start_scenario_instance', wait_finished=wait)
        start_scenario_push.configure(scenario_push)
        wait = [start_scenario_push]

    scenario_run = run(satellite_entity, satellite_ip, gateways)
    start_scenario_run = scenario.add_function('start_scenario_instance', wait_finished=wait)
    start_scenario_run.configure(scenario_run)
    
    if duration:
        stopper = scenario.add_function('stop_scenario_instance', wait_launched=[start_scenario_run], wait_delay=duration)
        stopper.configure(start_scenario_run)

    scenario_clear = clear(satellite_entity, satellite_interface, gateways, workstations)
    start_scenario_clear = scenario.add_function('start_scenario_instance', wait_finished=[start_scenario_run], wait_delay=5)
    start_scenario_clear.configure(scenario_clear)

    return scenario
