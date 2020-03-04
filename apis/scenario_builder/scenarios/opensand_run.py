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


""" Helpers to run opensand simple system """

from scenario_builder.helpers.access.opensand import opensand_run
from scenario_builder import Scenario
import ipaddress

SCENARIO_NAME = "Scenario run simple system"
SCENARIO_DESCRIPTION = """This configure simple system scenario allows to:
                       - Run opensand in the satellite, the gateways and the ST for an opensand test
                       """

def get_ip(ip):
    return str(ipaddress.ip_interface(ip).ip)

def build(gateways, sat_entity, sat_ip, scenario_name = SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    # Sat opensand
    opensand_run(scenario, sat_entity, 'sat', emulation_address = get_ip(sat_ip))
    id = 0
    for gw in gateways :
        # GW opensand
        if gw.gw_phy_entity is not None:
            opensand_run(scenario, gw.entity, 'gw-net-acc', entity_id = id, 
                        interconnection_address = get_ip(gw.ip[1]))
            opensand_run(scenario, gw.gw_phy_entity, 'gw-phy', entity_id = id, 
                        emulation_address = get_ip(gw.gw_phy_ip[1]), 
                        interconnection_address = get_ip(gw.gw_phy_ip[0]))
            id += 1            
        else:
            opensand_run(scenario, gw.entity, 'gw', entity_id = id, emulation_address = get_ip(gw.ip[1]))
            id += 1 

        # ST opensand
        for st in gw.st_list:
            opensand_run(scenario, st.entity, 'st', entity_id = id, emulation_address = get_ip(st.ip[1]))
            id += 1
    return scenario

