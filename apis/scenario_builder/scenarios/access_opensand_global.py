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

from scenario_builder import Scenario
from scenario_builder.scenarios.access_opensand import build as access_opensand, ST as _ST, GW as _GW, SPLIT_GW as _GW_PHY
from scenario_builder.scenarios.access_opensand_configure import configure, SAT, ST, GW, WS
from scenario_builder.scenarios.access_opensand_clear import clear


SCENARIO_DESCRIPTION = """This is reference OpenSAND scenario"""
SCENARIO_NAME = 'access_opensand_global'


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
    scenario_run = access_opensand(satellite, gws, sts, duration, configuration_files)
    start_scenario_run = scenario.add_function('start_scenario_instance', wait_finished=[start_scenario_configure])
    start_scenario_run.configure(scenario_run)
    
    scenario_clear = clear(satellite_entity, satellite_interface, gateways, workstations)
    start_scenario_clear = scenario.add_function('start_scenario_instance', wait_finished=[start_scenario_run], wait_delay=5)
    start_scenario_clear.configure(scenario_clear)

    return scenario
