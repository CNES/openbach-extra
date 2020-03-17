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
from collections import namedtuple

from scenario_builder import Scenario
from scenario_builder.helpers.access import opensand
from scenario_builder.scenarios.access_opensand import (
        build as access_opensand,
        SAT as _SAT, ST as _ST, GW as _GW, SPLIT_GW as _GW_PHY,
)


SCENARIO_DESCRIPTION = """This is reference OpenSAND scenario"""
SCENARIO_NAME = 'access_opensand_global'


CONFIGURE_DESCRIPTION = """This configure opensand system scenario allows to:
 - Configure the satellite, the gateways, the ST, the SRV and the CLT for an opensand test
"""
CONFIGURE_NAME = 'access_opensand_configure'


CLEAR_DESCRIPTION = """This clear simple system scenario allows to:
 - Clear the satellite, the gateways, the ST, the SRV and the CLT from an opensand test
"""
CLEAR_NAME = 'access_opensand_clear'


SAT = namedtuple('SAT', ('entity', 'interface', 'ip'))
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


def configure(satellite, gateways, work_stations=(), scenario_name=CONFIGURE_NAME):
    scenario = Scenario(scenario_name, CONFIGURE_DESCRIPTION)
    opensand.configure_satellite(scenario, satellite.entity, satellite.interface, satellite.ip)

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


def clear(satellite, gateways, work_stations=(), scenario_name=CLEAR_NAME):
    scenario = Scenario(scenario_name, CLEAR_DESCRIPTION)
    opensand.clear_satellite(scenario, satellite.entity, satellite.interface)

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


def _extract_ip(ip_with_mask):
    return ipaddress.ip_interface(ip_with_mask).ip.compressed


def _extract_simple_parameters(gateways):
    for gateway in gateways:
        _, emulation_address = map(_extract_ip, gateway.ips)
        if gateway.gateway_phy_entity is not None:
            interconnect_net_acc = emulation_address
            interconnect_phy, emulation_address = map(_extract_ip, gateway.gateway_phy_ips)
            yield _GW_PHY(
                    gateway.entity, gateway.gateway_phy_entity,
                    gateway.opensand_id, emulation_address,
                    interconnect_net_acc, interconnect_phy)
        else:
            yield _GW(gateway.entity, gateway.opensand_id, emulation_address)


def build(satellite, gateways, workstations=(), duration=0, configuration_files=None, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    scenario_configure = configure(satellite, gateways, workstations)
    start_scenario_configure = scenario.add_function('start_scenario_instance')
    start_scenario_configure.configure(scenario_configure)
 
    sts = [
            _ST(terminal.entity, terminal.opensand_id, _extract_ip(terminal.ips[1]))
            for gw in gateways
            for terminal in gw.terminals
    ]

    gws = list(_extract_simple_parameters(gateways))
    sat = _SAT(satellite.entity, _extract_ip(satellite.ip))
    scenario_run = access_opensand(sat, gws, sts, duration, configuration_files)
    start_scenario_run = scenario.add_function('start_scenario_instance', wait_finished=[start_scenario_configure])
    start_scenario_run.configure(scenario_run)
    
    scenario_clear = clear(satellite, gateways, workstations)
    start_scenario_clear = scenario.add_function('start_scenario_instance', wait_finished=[start_scenario_run], wait_delay=5)
    start_scenario_clear.configure(scenario_clear)

    return scenario
