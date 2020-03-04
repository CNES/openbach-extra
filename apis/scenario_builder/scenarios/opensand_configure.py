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


""" Helpers to configure opensand simple system """

from scenario_builder.helpers.network.ip_address import ip_address
from scenario_builder.helpers.network.ip_route import ip_route
from scenario_builder.helpers.access.opensand import opensand_network_ip
from scenario_builder import Scenario


SCENARIO_NAME = "Scenario configure simple system"
SCENARIO_DESCRIPTION = """This configure simple system scenario allows to:
                       - Configure the satellite, the gateways, the ST, the SRV and the CLT for a opensand test
                       """

def sat_configure(scenario, sat_entity, sat_interface, sat_ip):
    """
    Configure  the satellite:
    - ip_address with the interface and the ip
    """
    sat_conf = ip_address(scenario, sat_entity, sat_interface, 'add', sat_ip)

def st_configure(scenario, st_entity, interface, interface_ip, mask_ip, lan_ip, gw_ip):
    """ 
    interface[] and interface_ip[] are for ip_address
    mask_ip is for opensand job
    lan_ip[] and gw_ip are for ip_route
    """
    wait = None
    for interf, ip in zip(interface, interface_ip):
         wait = ip_address(scenario, st_entity, interf, 'add', ip, wait_finished = wait)
   
    wait = opensand_network_ip(scenario, st_entity, mask_ip, wait_finished = wait)

    for ip in lan_ip:
         wait = ip_route(scenario, st_entity, 'add', ip, gw_ip, wait_finished = wait)

def gw_phy_configure(scenario, gw_phy_entity, interface, interface_ip):
    wait = None
    for interf, ip in zip(interface, interface_ip):
         wait = ip_address(scenario, gw_phy_entity, interf, 'add', ip, wait_finished = wait)

def gw_configure(scenario, gw_entity, interface, interface_ip, mask_ip, lan_ip, gw_ip):
    wait = None 
    for interf, ip in zip(interface, interface_ip):
         wait = ip_address(scenario, gw_entity, interf, 'add', ip, wait_finished = wait)

    wait = opensand_network_ip(scenario, gw_entity, mask_ip, wait_finished = wait)
    for ip,gw_ip in zip(lan_ip,gw_ip):
         wait = ip_route(scenario, gw_entity, 'add', ip, gw_ip, wait_finished = wait)

def host_configure(scenario, entity, interface, interface_ip, ip_to_route, gw_ip):
    wait = ip_address(scenario, entity, interface, 'add', interface_ip)
    wait = ip_route(scenario, entity, 'add', ip_to_route, gw_ip, wait_finished = wait)

def build(gateways, sat_entity, sat_interface, sat_ip, scenario_name = SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    
    # Sat configure
    sat_configure(scenario, sat_entity, sat_interface, sat_ip)
    for gw in gateways :
        # Configure GW 
        gw_configure(scenario, gw.entity, gw.interface, gw.ip, gw.opensand_ip, gw.route_ip, gw.route_gw_ip)
        if gw.gw_phy_entity is not None:
            gw_phy_configure(scenario, gw.gw_phy_entity, gw.gw_phy_interface, gw.gw_phy_ip)
        
        # Configure ST
        for st in gw.st_list:
            st_configure(scenario, st.entity, st.interface, st.ip, st.opensand_ip, st.route_ip, st.route_gw_ip)

        # Configure SRV and CLT
        for host in gw.host_list:
            host_configure(scenario, host.entity, host.interface, host.ip, host.route_ip, host.route_gw_ip)
      
    return scenario
