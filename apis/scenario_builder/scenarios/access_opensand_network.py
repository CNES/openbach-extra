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


CONFIGURE_DESCRIPTION = """This configure opensand system scenario allows to:
 - Configure the satellite, the gateways, the ST, the SRV and the CLT for an opensand test
"""
CONFIGURE_NAME = 'access_opensand_configure'


CLEAR_DESCRIPTION = """This clear simple system scenario allows to:
 - Clear the satellite, the gateways, the ST, the SRV and the CLT from an opensand test
"""
CLEAR_NAME = 'access_opensand_clear'


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
