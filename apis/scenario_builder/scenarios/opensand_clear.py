#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016−2020 CNES
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


""" Helpers to clear opensand simple system """

from scenario_builder.helpers.network.ip_address import ip_address
from scenario_builder.helpers.access.opensand import opensand_network_clear
from scenario_builder import Scenario


SCENARIO_NAME = "Scenario clear simple system"
SCENARIO_DESCRIPTION = """This clear simple system scenario allows to:
                       - Clear the satellite, the gateways, the ST, the SRV and the CLT from an opensand test
                       """

def sat_clear(scenario, sat_entity, sat_interface):
    ip_address(scenario, sat_entity, sat_interface, 'flush')

def st_clear(scenario, st_entity, interface):
    wait = None
    for interf in interface:
         wait = ip_address(scenario, st_entity, interf, 'flush', wait_finished = wait)

    opensand_network_clear(scenario, st_entity, wait_finished = wait)


def gw_phy_clear(scenario, gw_phy_entity, interface):
    wait = None
    for interf in interface:
         wait = ip_address(scenario, gw_phy_entity, interf, 'flush', wait_finished = wait)

def gw_clear(scenario, gw_entity, interface):
    wait = None
    for interf in interface:
         wait = ip_address(scenario, gw_entity, interf, 'flush', wait_finished = wait)

    opensand_network_clear(scenario, gw_entity, wait_finished = wait)


def host_clear(scenario, entity, interface):
    wait = ip_address(scenario, entity, interface, 'flush')


def build(gateways, sat_entity, sat_interface, scenario_name = SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    # Sat clear
    sat_clear(scenario, sat_entity, sat_interface)
    for gw in gateways :
        # Clear GW
        gw_clear(scenario, gw.entity, gw.interface)
        if gw.gw_phy_entity is not None:
            gw_phy_clear(scenario, gw.gw_phy_entity, gw.gw_phy_interface)

        # Clear ST
        for st in gw.st_list:
            st_clear(scenario, st.entity, st.interface)

        # Clear SRV and CLT
        for host in gw.host_list:
            host_clear(scenario, host.entity, host.interface)

    return scenario

