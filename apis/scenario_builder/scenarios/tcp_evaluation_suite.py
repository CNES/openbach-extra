#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2020 CNES
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

from scenario_builder import Scenario
from scenario_builder.scenarios import transport_tcp_stack_conf, network_configure_link, service_data_transfer


SCENARIO_NAME = 'tcp_evaluation_suite'
SCENARIO_DESCRIPTION = """This scenario is a wrapper for the following scenarios:
 - transport_tcp_stack_conf
 - network_configure_link
 - service_data_transfer
Scenario that permit us to evaluate tcp links.
"""

def build(
        endpointA, endpointB, endpointC, 
        endpointD, routerL, routerR, 
        endpointA_network_ip, endpointB_network_ip, 
        endpointC_network_ip, endpointD_network_ip, 
        routerL_ens3_ip, routerL_ens6_ip, 
        routerR_ens6_ip, routerR_ens3_ip, 
        routerL_ens4_ip, routerR_ens5_ip,
        congestion_control,
        scenario_name=SCENARIO_NAME):


    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)


    ########################################
    ####### transport_tcp_stack_conf #######
    ########################################
    """
    endpointA and endpointC parameters:
      - Congestion control : CUBIC
      - IW : 10
    endpointB and endpointD parameters:
      - Congestion control : CUBIC
      - IW : 10
    """

    route_AL = {
            "destination_ip": endpointC_network_ip, #192.168.3.0/24
            "gateway_ip": routerL_ens3_ip, #192.168.0.14
            "operation": 'change', 
            "initcwnd": 10
            }
    interface_A = 'ens3'

    route_BL = {
            "destination_ip": endpointD_network_ip, #192.168.4.0/24
            "gateway_ip": routerL_ens6_ip, #192.168.1.5
            "operation": 'change',
            "initcwnd": 10
            }
    interface_B = 'ens4'

    route_CR = {
            "destination_ip": endpointA_network_ip, #192.168.0.0/24
            "gateway_ip": routerR_ens6_ip, #192.168.3.3
            "operation": 'change',
            "initcwnd": 10
            }
    interface_C = 'ens3'

    route_DR = {
            "destination_ip": endpointB_network_ip, #192.168.1.0/24
            "gateway_ip": routerR_ens3_ip, #192.168.4.8
            "operation": 'change',
            "initcwnd": 10
            }
    interface_D = 'ens3'

    route_RA = {
            "destination_ip": endpointA_network_ip, #192.168.0.0/24
            "gateway_ip": routerL_ens4_ip, #192.168.2.15
            "operation": 'change',
            "initcwnd": 10
            }
    interface_R = 'ens5'

    route_RB = {
            "destination_ip": endpointB_network_ip, #192.168.1.0/24
            "gateway_ip": routerL_ens4_ip, #192.168.2.15
            "operation": 'change',
            "initcwnd": 10
            }

    route_LC = {
            "destination_ip": endpointC_network_ip, #192.168.3.0/24
            "gateway_ip": routerR_ens5_ip, #192.168.2.25
            "operation": 'change',
            "initcwnd": 10
            }
    interface_L = 'ens4'

    route_LD = {
            "destination_ip": endpointD_network_ip, #192.168.4.0/24
            "gateway_ip": routerR_ens5_ip, #192.168.2.25
            "operation": 'change',
            "initcwnd": 10
            }

    # transport_tcp_stack_conf on endpointA to L
    scenario_tcp_conf_A = transport_tcp_stack_conf.build(endpointA, congestion_control, interface=interface_A, route=route_AL, scenario_name='transport_tcp_stack_conf_A')
    start_tcp_conf_A = scenario.add_function('start_scenario_instance')
    start_tcp_conf_A.configure(scenario_tcp_conf_A)

    # transport_tcp_stack_conf on endpointB to L
    scenario_tcp_conf_B = transport_tcp_stack_conf.build(endpointB, congestion_control, interface=interface_B, route=route_BL, scenario_name='transport_tcp_stack_conf_B')
    start_tcp_conf_B = scenario.add_function('start_scenario_instance')
    start_tcp_conf_B.configure(scenario_tcp_conf_B)

    # transport_tcp_stack_conf on endpointC to R
    scenario_tcp_conf_C = transport_tcp_stack_conf.build(endpointC, congestion_control, interface=interface_C, route=route_CR, scenario_name='transport_tcp_stack_conf_C')
    start_tcp_conf_C = scenario.add_function('start_scenario_instance')
    start_tcp_conf_C.configure(scenario_tcp_conf_C)

    # transport_tcp_stack_conf on endpointD to R
    scenario_tcp_conf_D = transport_tcp_stack_conf.build(endpointD, congestion_control, interface=interface_D, route=route_DR, scenario_name='transport_tcp_stack_conf_D')
    start_tcp_conf_D = scenario.add_function('start_scenario_instance')
    start_tcp_conf_D.configure(scenario_tcp_conf_D)

    # transport_tcp_stack_conf on routerR to A
    scenario_tcp_conf_RA = transport_tcp_stack_conf.build(routerR, congestion_control, interface=interface_R, route=route_RA, scenario_name='transport_tcp_stack_conf_RA')
    start_tcp_conf_RA = scenario.add_function('start_scenario_instance')
    start_tcp_conf_RA.configure(scenario_tcp_conf_RA)

    # transport_tcp_stack_conf on routerR to B
    scenario_tcp_conf_RB = transport_tcp_stack_conf.build(routerR, congestion_control, interface=interface_R, route=route_RB, scenario_name='transport_tcp_stack_conf_RB')
    start_tcp_conf_RB = scenario.add_function('start_scenario_instance')
    start_tcp_conf_RB.configure(scenario_tcp_conf_RB)

    # transport_tcp_stack_conf on routerL to C
    scenario_tcp_conf_LC = transport_tcp_stack_conf.build(routerL, congestion_control, interface=interface_L, route=route_LC, scenario_name='transport_tcp_stack_conf_LC')
    start_tcp_conf_LC = scenario.add_function('start_scenario_instance')
    start_tcp_conf_LC.configure(scenario_tcp_conf_LC)

    # transport_tcp_stack_conf on routerL to D
    scenario_tcp_conf_LD = transport_tcp_stack_conf.build(routerL, congestion_control, interface=interface_L, route=route_LD, scenario_name='transport_tcp_stack_conf_LD')
    start_tcp_conf_LD = scenario.add_function('start_scenario_instance')
    start_tcp_conf_LD.configure(scenario_tcp_conf_LD)

##### TODO #####

#    ########################################
#    ######## network_configure_link ########
#    ########################################
#
#    # network_configure_link L -> A
#    scenario_network_conf_link_LA = network_configure_link.build(routerL, endpointA)
#    start_network_conf_link_LA = scenario.add_function('start_scenario_instance')
#    start_network_conf_link_LA.configure(scenario_network_conf_link_LA)
#    # network_configure_link L -> B
#    scenario_network_conf_link_LB = network_configure_link.build(routerL, endpointB)
#    start_network_conf_link_LB = scenario.add_function('start_scenario_instance')
#    start_network_conf_link_LB.configure(scenario_network_conf_link_LB)
#
#    # network_configure_link R -> C
#    scenario_network_conf_link_RC = network_configure_link.build(routerR, endpointC)
#    start_network_conf_link_RC = scenario.add_function('start_scenario_instance')
#    start_network_conf_link_RC.configure(scenario_network_conf_link_RC)
#    # network_configure_link R -> D
#    scenario_network_conf_link_RD = network_configure_link.build(routerR, endpointD)
#    start_network_conf_link_RD = scenario.add_function('start_scenario_instance')
#    start_network_conf_link_RD.configure(scenario_network_conf_link_RD)
#
##    # network_configure_link A -> L
##    scenario_network_conf_link_AL = network_configure_link.build(endpointA, routerL)
##    start_network_conf_link_AL = scenario.add_function('start_scenario_instance')
##    start_network_conf_link_AL.configure(scenario_network_conf_link_AL)
##
##    # network_configure_link B -> L
##    scenario_network_conf_link_BL = network_configure_link.build(endpointB, routerL)
##    start_network_conf_link_BL = scenario.add_function('start_scenario_instance')
##    start_network_conf_link_BL.configure(scenario_network_conf_link_BL)
##
##    # network_configure_link C -> R
##    scenario_network_conf_link_CR = network_configure_link.build(endpointC, routerR)
##    start_network_conf_link_CR = scenario.add_function('start_scenario_instance')
##    start_network_conf_link_CR.configure(scenario_network_conf_link_CR)
##
##    # network_configure_link D -> R
##    scenario_network_conf_link_DR = network_configure_link.build(endpointd, routerR)
##    start_network_conf_link_DR = scenario.add_function('start_scenario_instance')
##    start_network_conf_link_DR.configure(scenario_network_conf_link_DR)

#    # network_configure_link L -> R
#    scenario_network_conf_link_LR = network_configure_link.build(routerL, routerR)
#    start_network_conf_link_LR = scenario.add_function('start_scenario_instance')
#    start_network_conf_link_LR.configure(scenario_network_conf_link_LR)
#    # network_configure_link L -> R t+10
#    scenario_network_conf_link_LR10 = network_configure_link.build(routerL, routerR)
#    start_network_conf_link_LR10 = scenario.add_function('start_scenario_instance', wait_finished=['start_network_conf_link_LR'], wait_delay=10)
#    start_network_conf_link_LR10.configure(scenario_network_conf_link_LR10)
#    # network_configure_link L -> R t10+10
#    scenario_network_conf_link_LR1010 = network_configure_link.build(routerL, routerR)
#    start_network_conf_link_LR1010 = scenario.add_function('start_scenario_instance', wait_finished=['start_network_conf_link_LR10'], wait_delay=10)
#    start_network_conf_link_LR1010.configure(scenario_network_conf_link_LR1010)
#

#    ########################################
#    ######## service_data_transfer #########
#    ########################################
#
#    # service_data_transfer A -> C
#    scenario_service_data_transfer_AC = service_data_transfer.build(endpointA, endpointC)
#    start_service_data_transfer_AC = scenario.add_function('start_scenario_instance')
#    start_service_data_transfer_AC.configure(scenario_service_data_transfer_AC, wait_finished=['start_tcp_conf_A', 'start_tcp_conf_C','start_network_conf_link_AC'])
#
#    # service_data_transfer B -> D
#    scenario_service_data_transfer_BD = service_data_transfer.build(endpointB, endpointD)
#    start_service_data_transfer_BD = scenario.add_function('start_scenario_instance')
#    start_service_data_transfer_BD.configure(scenario_service_data_transfer_BD,
#            wait_finished=['start_tcp_conf_B', 'start_tcp_conf_D','start_network_conf_link_BD', 'start_service_data_transfer_AC'])
#
#    # service_data_transfer A -> C
#    scenario_service_data_transfer_AC = service_data_transfer.build(endpointA, endpointC)
#    start_service_data_transfer_AC = scenario.add_function('start_scenario_instance')
#    start_service_data_transfer_AC.configure(scenario_service_data_transfer_AC,
#            wait_finished=['start_service_data_transfer_BD'], wait_delay=5)
#    # 10 fois.


    return scenario


