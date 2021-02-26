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
It provides a scenario that enables the evaluation of TCP
congestion controls.
"""

def build(
        endpointA, endpointB, endpointC,
        endpointD, routerL, routerR,
        endpointC_ip, endpointD_ip, server_port,
        endpointA_network_ip, endpointB_network_ip,
        endpointC_network_ip, endpointD_network_ip,
        routerL_to_endpointA_ip, routerL_to_endpointB_ip,
        routerR_to_endpointC_ip, routerR_to_endpointD_ip,
        routerL_to_routerR_ip, routerR_to_routerL_ip,
        interface_AL, interface_BL, interface_CR,
        interface_DR, interface_RA, interface_RB,
        interface_LC, interface_LD, interface_LA,
        interface_LB, interface_RC, interface_RD,
        interface_LR, interface_RL, congestion_control,
        scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)


    ########################################
    ####### transport_tcp_stack_conf #######
    ########################################

    route_AL = {
            "destination_ip": endpointC_network_ip, #192.168.3.0/24
            "gateway_ip": routerL_to_endpointA_ip, #192.168.0.14
            "operation": 'change', 
            "initcwnd": 10
            }

    route_BL = {
            "destination_ip": endpointD_network_ip, #192.168.4.0/24
            "gateway_ip": routerL_to_endpointB_ip, #192.168.1.5
            "operation": 'change',
            "initcwnd": 10
            }

    route_CR = {
            "destination_ip": endpointA_network_ip, #192.168.0.0/24
            "gateway_ip": routerR_to_endpointC_ip, #192.168.3.3
            "operation": 'change',
            "initcwnd": 10
            }

    route_DR = {
            "destination_ip": endpointB_network_ip, #192.168.1.0/24
            "gateway_ip": routerR_to_endpointD_ip, #192.168.4.8
            "operation": 'change',
            "initcwnd": 10
            }

    route_RA = {
            "destination_ip": endpointA_network_ip, #192.168.0.0/24
            "gateway_ip": routerL_to_routerR_ip, #192.168.2.15
            "operation": 'change',
            "initcwnd": 10
            }

    route_RB = {
            "destination_ip": endpointB_network_ip, #192.168.1.0/24
            "gateway_ip": routerL_to_routerR_ip, #192.168.2.15
            "operation": 'change',
            "initcwnd": 10
            }

    route_LC = {
            "destination_ip": endpointC_network_ip, #192.168.3.0/24
            "gateway_ip": routerR_to_routerL_ip, #192.168.2.25
            "operation": 'change',
            "initcwnd": 10
            }

    route_LD = {
            "destination_ip": endpointD_network_ip, #192.168.4.0/24
            "gateway_ip": routerR_to_routerL_ip, #192.168.2.25
            "operation": 'change',
            "initcwnd": 10
            }

    # transport_tcp_stack_conf on endpointA to L
    scenario_tcp_conf_A = transport_tcp_stack_conf.build(
            endpointA,
            congestion_control,
            interface=interface_AL, #ens3
            route=route_AL,
            scenario_name='transport_tcp_stack_conf_A')
    start_tcp_conf_A = scenario.add_function('start_scenario_instance')
    start_tcp_conf_A.configure(scenario_tcp_conf_A)

    # transport_tcp_stack_conf on endpointB to L
    scenario_tcp_conf_B = transport_tcp_stack_conf.build(
            endpointB,
            congestion_control,
            interface=interface_BL, #ens4
            route=route_BL,
            scenario_name='transport_tcp_stack_conf_B')
    start_tcp_conf_B = scenario.add_function('start_scenario_instance')
    start_tcp_conf_B.configure(scenario_tcp_conf_B)

    # transport_tcp_stack_conf on endpointC to R
    scenario_tcp_conf_C = transport_tcp_stack_conf.build(
            endpointC,
            congestion_control,
            interface=interface_CR, #ens3
            route=route_CR,
            scenario_name='transport_tcp_stack_conf_C')
    start_tcp_conf_C = scenario.add_function('start_scenario_instance')
    start_tcp_conf_C.configure(scenario_tcp_conf_C)

    # transport_tcp_stack_conf on endpointD to R
    scenario_tcp_conf_D = transport_tcp_stack_conf.build(
            endpointD,
            congestion_control,
            interface=interface_DR, #ens3
            route=route_DR,
            scenario_name='transport_tcp_stack_conf_D')
    start_tcp_conf_D = scenario.add_function('start_scenario_instance')
    start_tcp_conf_D.configure(scenario_tcp_conf_D)

    # transport_tcp_stack_conf on routerR to A
    scenario_tcp_conf_RA = transport_tcp_stack_conf.build(
            routerR,
            congestion_control,
            interface=interface_RA, #ens5
            route=route_RA,
            scenario_name='transport_tcp_stack_conf_RA')
    start_tcp_conf_RA = scenario.add_function('start_scenario_instance')
    start_tcp_conf_RA.configure(scenario_tcp_conf_RA)

    # transport_tcp_stack_conf on routerR to B
    scenario_tcp_conf_RB = transport_tcp_stack_conf.build(
            routerR,
            congestion_control,
            interface=interface_RB, #ens5
            route=route_RB,
            scenario_name='transport_tcp_stack_conf_RB')
    start_tcp_conf_RB = scenario.add_function('start_scenario_instance')
    start_tcp_conf_RB.configure(scenario_tcp_conf_RB)

    # transport_tcp_stack_conf on routerL to C
    scenario_tcp_conf_LC = transport_tcp_stack_conf.build(
            routerL,
            congestion_control,
            interface=interface_LC, #ens4
            route=route_LC,
            scenario_name='transport_tcp_stack_conf_LC')
    start_tcp_conf_LC = scenario.add_function('start_scenario_instance')
    start_tcp_conf_LC.configure(scenario_tcp_conf_LC)

    # transport_tcp_stack_conf on routerL to D
    scenario_tcp_conf_LD = transport_tcp_stack_conf.build(
            routerL,
            congestion_control,
            interface=interface_LD, #ens4
            route=route_LD,
            scenario_name='transport_tcp_stack_conf_LD')
    start_tcp_conf_LD = scenario.add_function('start_scenario_instance')
    start_tcp_conf_LD.configure(scenario_tcp_conf_LD)


    ########################################
    ######## network_configure_link ########
    ########################################

    # network_configure_link L -> A & L -> B
    scenario_network_conf_link_LAB = network_configure_link.build(
            entity=routerL,
            ifaces='{},{}'.format(interface_LA, interface_LB), #'ens3, ens6'
            mode='all',
            operation='apply',
            bandwidth='100M',
            delay=10, #latency
            scenario_name='network_configure_link_LAB')
    start_network_conf_link_LAB = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[
                start_tcp_conf_A,
                start_tcp_conf_B,
                start_tcp_conf_C,
                start_tcp_conf_D,
                start_tcp_conf_RA,
                start_tcp_conf_RB,
                start_tcp_conf_LC,
                start_tcp_conf_LD
            ])
    start_network_conf_link_LAB.configure(scenario_network_conf_link_LAB)

    # network_configure_link R -> C & R -> D
    scenario_network_conf_link_RCD = network_configure_link.build(
            entity=routerR,
            ifaces='{},{}'.format(interface_RC, interface_RD), #'ens6, ens3'
            mode='all',
            operation='apply',
            bandwidth='100M',
            delay=10,
            scenario_name='network_configure_link_RCD')
    start_network_conf_link_RCD = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[
                start_tcp_conf_A,
                start_tcp_conf_B,
                start_tcp_conf_C,
                start_tcp_conf_D,
                start_tcp_conf_RA,
                start_tcp_conf_RB,
                start_tcp_conf_LC,
                start_tcp_conf_LD
            ])
    start_network_conf_link_RCD.configure(scenario_network_conf_link_RCD)

    # network_configure_link L -> R
    scenario_network_conf_link_LR = network_configure_link.build(
            entity=routerR,
            ifaces=interface_LR, #'ens4'
            mode='egress',
            operation='apply',
            bandwidth='20M',
            delay=10,
            scenario_name='network_configure_link_LR')
    start_network_conf_link_LR = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[
                start_tcp_conf_A,
                start_tcp_conf_B,
                start_tcp_conf_C,
                start_tcp_conf_D,
                start_tcp_conf_RA,
                start_tcp_conf_RB,
                start_tcp_conf_LC,
                start_tcp_conf_LD
            ])
    start_network_conf_link_LR.configure(scenario_network_conf_link_LR)

    # network_configure_link R -> L
    scenario_network_conf_link_RL = network_configure_link.build(
            entity=routerL,
            ifaces=interface_RL, #'ens5'
            mode='egress',
            operation='apply',
            bandwidth='20M',
            delay=10,
            scenario_name='network_configure_link_RL')
    start_network_conf_link_RL = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[
                start_tcp_conf_A,
                start_tcp_conf_B,
                start_tcp_conf_C,
                start_tcp_conf_D,
                start_tcp_conf_RA,
                start_tcp_conf_RB,
                start_tcp_conf_LC,
                start_tcp_conf_LD
            ])
    start_network_conf_link_RL.configure(scenario_network_conf_link_RL)


    ########################################
    ######## service_data_transfer #########
    ########################################

    # service_data_transfer B -> D
    scenario_service_data_transfer_BD = service_data_transfer.build(
            server_entity=endpointD,
            client_entity=endpointB,
            server_ip=endpointD_ip,
            server_port=server_port,
            duration=None,
            file_size='500M',
            tos=0,
            mtu=1400,
            scenario_name='service_data_transfer_BD')
    start_service_data_transfer_BD = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[
                start_network_conf_link_LAB,
                start_network_conf_link_RCD,
                start_network_conf_link_LR,
                start_network_conf_link_RL
            ])
    start_service_data_transfer_BD.configure(scenario_service_data_transfer_BD)


    ########################################
    ######## network_configure_link ########
    ########################################

    # network_configure_link L -> R t=0+10s
    scenario_network_conf_link_LR_10 = network_configure_link.build(
            entity=routerR,
            ifaces=interface_LR, #'ens4'
            mode='egress',
            operation='apply',
            bandwidth='10M',
            delay=10,
            scenario_name='network_configure_link_LR_10')
    start_network_conf_link_LR_10 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_BD],
            wait_delay=10)
    start_network_conf_link_LR_10.configure(scenario_network_conf_link_LR_10)

    # network_configure_link R -> L t=0+10s
    scenario_network_conf_link_RL_10 = network_configure_link.build(
            entity=routerL,
            ifaces=interface_RL, #'ens5'
            mode='egress',
            operation='apply',
            bandwidth='10M',
            delay=10,
            scenario_name='network_configure_link_RL_10')
    start_network_conf_link_RL_10 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_BD],
            wait_delay=10)
    start_network_conf_link_RL_10.configure(scenario_network_conf_link_RL_10)


    # network_configure_link L -> R t=10+10s
    scenario_network_conf_link_LR_1010 = network_configure_link.build(
            entity=routerR,
            ifaces=interface_LR, #'ens4'
            mode='egress',
            operation='apply',
            bandwidth='20M',
            delay=10,
            scenario_name='network_configure_link_LR_1010')
    start_network_conf_link_LR_1010 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_network_conf_link_LR_10, start_network_conf_link_RL_10],
            wait_delay=10)
    start_network_conf_link_LR_1010.configure(scenario_network_conf_link_LR_1010)

    # network_configure_link R -> L t=10+10s
    scenario_network_conf_link_RL_1010 = network_configure_link.build(
            entity=routerL,
            ifaces=interface_RL, #'ens5'
            mode='egress',
            operation='apply',
            bandwidth='20M',
            delay=10,
            scenario_name='network_configure_link_RL_1010')
    start_network_conf_link_RL_1010 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_network_conf_link_LR_10, start_network_conf_link_RL_10],
            wait_delay=10)
    start_network_conf_link_RL_1010.configure(scenario_network_conf_link_RL_1010)

    ########################################
    ######## network_configure_link ########
    ########################################

    # service_data_transfer A -> C, first
    scenario_service_data_transfer_AC = service_data_transfer.build(
            server_entity=endpointC,
            client_entity=endpointA,
            server_ip=endpointC_ip,
            server_port=server_port,
            duration=None,
            file_size='10M',
            tos=0,
            mtu=1400,
            scenario_name='service_data_transfer_AC')

    start_service_data_transfer_AC_1 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_BD],
            wait_delay=5)
    start_service_data_transfer_AC_1.configure(scenario_service_data_transfer_AC)

    # service_data_transfer A -> C, 2 to 10
    start_service_data_transfer_AC_2 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_1],
            wait_delay=5)
    start_service_data_transfer_AC_2.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_3 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_2],
            wait_delay=5)
    start_service_data_transfer_AC_3.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_4 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_3],
            wait_delay=5)
    start_service_data_transfer_AC_4.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_5 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_4],
            wait_delay=5)
    start_service_data_transfer_AC_5.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_6 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_5],
            wait_delay=5)
    start_service_data_transfer_AC_6.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_7 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_6],
            wait_delay=5)
    start_service_data_transfer_AC_7.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_8 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_7],
            wait_delay=5)
    start_service_data_transfer_AC_8.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_9 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_8],
            wait_delay=5)
    start_service_data_transfer_AC_9.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_10 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_9],
            wait_delay=5)
    start_service_data_transfer_AC_10.configure(scenario_service_data_transfer_AC)

    return scenario
