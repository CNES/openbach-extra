#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2023 CNES
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
from scenario_builder.openbach_functions import StartJobInstance
from scenario_builder.openbach_functions import StartScenarioInstance
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.helpers.transport.iperf3 import iperf3_find_client
from scenario_builder.scenarios import transport_tcp_stack_conf, network_configure_link, service_data_transfer, rate_monitoring, transport_pep

SCENARIO_NAME = 'tcp_evaluation_suite'
SCENARIO_DESCRIPTION = """This scenario is a wrapper for the following scenarios:
 - transport_tcp_stack_conf
 - network_configure_link
 - service_data_transfer
 - transport_pep
It provides a scenario that enables the evaluation of TCP
congestion controls.
"""


def _iperf3_legend(openbach_function):
    iperf3 = openbach_function.start_job_instance['iperf3']
    destination = openbach_function.start_job_instance['entity_name']
    legend = {'endpoint': 'client', 'address': iperf3['client']['server_ip'], 'destination': destination, 'transmitted_size': iperf3['client']['transmitted_size']}
    return 'Data Transfer - {endpoint} {address} {destination} {transmitted_size}'.format_map(legend)


def _rate_monitoring_legend(openbach_function):
    rate_monitoring = openbach_function.start_job_instance['rate_monitoring']
    destination = openbach_function.start_job_instance['entity_name']
    legend = {'destination': destination}
    return 'Rate Monitoring - {destination}'.format_map(legend)


def build(
        endpointA, endpointB, endpointC, endpointD,
        endpointC_ip, endpointD_ip, routerL, routerR,
        endpointA_network_ip, endpointB_network_ip,
        endpointC_network_ip, endpointD_network_ip,
        routerL_to_endpointA_ip, routerL_to_endpointB_ip,
        routerR_to_endpointC_ip, routerR_to_endpointD_ip,
        routerL_to_routerR_ip, routerR_to_routerL_ip,
        interface_AL, interface_BL, interface_CR,
        interface_DR, interface_RA, interface_RB,
        interface_LC, interface_LD, interface_LA,
        interface_LB, interface_RC, interface_RD,
        interface_LR, interface_RL, BD_file_size,
        AC_file_size, delay, loss, bandwidth, initcwnd,
        wait_delay_LR, congestion_control, server_port, pep,
        post_processing_entity, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    ########################################
    ####### transport_tcp_stack_conf #######
    ########################################

    route_AL = {
            "destination_ip": endpointC_network_ip, #192.168.3.0/24
            "gateway_ip": routerL_to_endpointA_ip, #192.168.0.14
            "operation": 'change', 
            "initcwnd": initcwnd
            }

    route_BL = {
            "destination_ip": endpointD_network_ip, #192.168.4.0/24
            "gateway_ip": routerL_to_endpointB_ip, #192.168.1.5
            "operation": 'change',
            "initcwnd": initcwnd
            }

    route_CR = {
            "destination_ip": endpointA_network_ip, #192.168.0.0/24
            "gateway_ip": routerR_to_endpointC_ip, #192.168.3.3
            "operation": 'change',
            "initcwnd": initcwnd
            }

    route_DR = {
            "destination_ip": endpointB_network_ip, #192.168.1.0/24
            "gateway_ip": routerR_to_endpointD_ip, #192.168.4.8
            "operation": 'change',
            "initcwnd": initcwnd
            }

    route_RA = {
            "destination_ip": endpointA_network_ip, #192.168.0.0/24
            "gateway_ip": routerL_to_routerR_ip, #192.168.2.15
            "operation": 'change',
            "initcwnd": initcwnd
            }

    route_RB = {
            "destination_ip": endpointB_network_ip, #192.168.1.0/24
            "gateway_ip": routerL_to_routerR_ip, #192.168.2.15
            "operation": 'change',
            "initcwnd": initcwnd
            }

    route_LC = {
            "destination_ip": endpointC_network_ip, #192.168.3.0/24
            "gateway_ip": routerR_to_routerL_ip, #192.168.2.25
            "operation": 'change',
            "initcwnd": initcwnd
            }

    route_LD = {
            "destination_ip": endpointD_network_ip, #192.168.4.0/24
            "gateway_ip": routerR_to_routerL_ip, #192.168.2.25
            "operation": 'change',
            "initcwnd": initcwnd
            }

    # transport_tcp_stack_conf on endpointA to L
    scenario_tcp_conf_A = transport_tcp_stack_conf.build(
            endpointA,
            congestion_control,
            interface=interface_AL, #ens3
            route=route_AL,
            tcp_slow_start_after_idle=1,
            tcp_no_metrics_save=1,
            scenario_name='transport_tcp_stack_conf_A')
    start_tcp_conf_A = scenario.add_function('start_scenario_instance')
    start_tcp_conf_A.configure(scenario_tcp_conf_A)

    # transport_tcp_stack_conf on endpointB to L
    scenario_tcp_conf_B = transport_tcp_stack_conf.build(
            endpointB,
            congestion_control,
            interface=interface_BL, #ens4
            route=route_BL,
            tcp_slow_start_after_idle=1,
            tcp_no_metrics_save=1,
            scenario_name='transport_tcp_stack_conf_B')
    start_tcp_conf_B = scenario.add_function('start_scenario_instance')
    start_tcp_conf_B.configure(scenario_tcp_conf_B)

    # transport_tcp_stack_conf on endpointC to R
    scenario_tcp_conf_C = transport_tcp_stack_conf.build(
            endpointC,
            congestion_control,
            interface=interface_CR, #ens3
            route=route_CR,
            tcp_slow_start_after_idle=1,
            tcp_no_metrics_save=1,
            scenario_name='transport_tcp_stack_conf_C')
    start_tcp_conf_C = scenario.add_function('start_scenario_instance')
    start_tcp_conf_C.configure(scenario_tcp_conf_C)

    # transport_tcp_stack_conf on endpointD to R
    scenario_tcp_conf_D = transport_tcp_stack_conf.build(
            endpointD,
            congestion_control,
            interface=interface_DR, #ens3
            route=route_DR,
            tcp_slow_start_after_idle=1,
            tcp_no_metrics_save=1,
            scenario_name='transport_tcp_stack_conf_D')
    start_tcp_conf_D = scenario.add_function('start_scenario_instance')
    start_tcp_conf_D.configure(scenario_tcp_conf_D)

    # transport_tcp_stack_conf on routerR to A
    scenario_tcp_conf_RA = transport_tcp_stack_conf.build(
            routerR,
            congestion_control,
            interface=interface_RA, #ens5
            route=route_RA,
            tcp_slow_start_after_idle=1,
            tcp_no_metrics_save=1,
            scenario_name='transport_tcp_stack_conf_RA')
    start_tcp_conf_RA = scenario.add_function('start_scenario_instance')
    start_tcp_conf_RA.configure(scenario_tcp_conf_RA)

    # transport_tcp_stack_conf on routerR to B
    scenario_tcp_conf_RB = transport_tcp_stack_conf.build(
            routerR,
            congestion_control,
            interface=interface_RB, #ens5
            route=route_RB,
            tcp_slow_start_after_idle=1,
            tcp_no_metrics_save=1,
            scenario_name='transport_tcp_stack_conf_RB')
    start_tcp_conf_RB = scenario.add_function('start_scenario_instance')
    start_tcp_conf_RB.configure(scenario_tcp_conf_RB)

    # transport_tcp_stack_conf on routerL to C
    scenario_tcp_conf_LC = transport_tcp_stack_conf.build(
            routerL,
            congestion_control,
            interface=interface_LC, #ens4
            route=route_LC,
            tcp_slow_start_after_idle=1,
            tcp_no_metrics_save=1,
            scenario_name='transport_tcp_stack_conf_LC')
    start_tcp_conf_LC = scenario.add_function('start_scenario_instance')
    start_tcp_conf_LC.configure(scenario_tcp_conf_LC)

    # transport_tcp_stack_conf on routerL to D
    scenario_tcp_conf_LD = transport_tcp_stack_conf.build(
            routerL,
            congestion_control,
            interface=interface_LD, #ens4
            route=route_LD,
            tcp_slow_start_after_idle=1,
            tcp_no_metrics_save=1,
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
            bandwidth=bandwidth[0], #20M
            loss_model_params=loss[0], #0
            delay=delay[0], #10
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
            bandwidth=bandwidth[0], #20M
            loss_model_params=loss[0], #0
            delay=delay[0], #10
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
    ################# pep ##################
    ########################################

    if pep:
        # pep on R: redirect traffic from A to C /// ou c'est de R à C ? Ou de L à R ?
        scenario_pep_RL = transport_pep.build(
                entity=routerR,
                redirect_ifaces='{}, {}, {}'.format(interface_RC, interface_RD, interface_RL), #'ens3, ens6, ens4'
                scenario_name='pep_RL')
        start_pep_RL = scenario.add_function(
                'start_scenario_instance',
                wait_finished=[
                    start_network_conf_link_LR,
                    start_network_conf_link_RL
                ])
        start_pep_RL.configure(scenario_pep_RL)
                
        # pep on L: redirect traffic from B to D
        scenario_pep_LR = transport_pep.build(
                entity=routerL,
                redirect_ifaces='{}, {}, {}'.format(interface_LA, interface_LB, interface_LR), #'ens3, ens6, ens4'
                scenario_name='pep_LR')
        start_pep_LR = scenario.add_function(
                'start_scenario_instance',
                wait_finished=[
                    start_network_conf_link_LR,
                    start_network_conf_link_RL
                ])
        start_pep_LR.configure(scenario_pep_LR)

    ########################################
    ########### rate_monitoring ############
    ########################################
    # We launch rate_monitoring jobs before launching
    # traffic to retreive interesting statistics.

    # rate_monitoring on C (for link C-R)
    scenario_rate_monitoring_C = rate_monitoring.build(
            entity=endpointC,
            sampling_interval=1,
            chain_name='INPUT',
            in_interface=interface_CR,
            scenario_name='rate_monitoring_C')
    start_rate_monitoring_C = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[
                start_network_conf_link_LAB,
                start_network_conf_link_RCD,
                start_network_conf_link_LR,
                start_network_conf_link_RL
            ])
    start_rate_monitoring_C.configure(scenario_rate_monitoring_C)

    # rate_monitoring on D (for link D-R)
    scenario_rate_monitoring_D = rate_monitoring.build(
            entity=endpointD,
            sampling_interval=1,
            chain_name='INPUT',
            in_interface=interface_DR,
            scenario_name='rate_monitoring_D')
    start_rate_monitoring_D = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[
                start_network_conf_link_LAB,
                start_network_conf_link_RCD,
                start_network_conf_link_LR,
                start_network_conf_link_RL
            ])
    start_rate_monitoring_D.configure(scenario_rate_monitoring_D)

    # rate_monitoring on R (for link R-L)
    routerR_chain = 'INPUT' if pep else 'FORWARD'
    scenario_rate_monitoring_R = rate_monitoring.build(
            entity=routerR,
            sampling_interval=1,
            chain_name=routerR_chain,
            in_interface=interface_RL,
            scenario_name='rate_monitoring_R')
    start_rate_monitoring_R = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[
                start_network_conf_link_LAB,
                start_network_conf_link_RCD,
                start_network_conf_link_LR,
                start_network_conf_link_RL
            ])
    start_rate_monitoring_R.configure(scenario_rate_monitoring_R)

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
            file_size=BD_file_size, #5000M
            tos=0,
            mtu=1400,
            scenario_name='service_data_transfer_BD')
    start_service_data_transfer_BD = scenario.add_function(
            'start_scenario_instance',
            wait_launched=[
                start_rate_monitoring_C,
                start_rate_monitoring_D,
                start_rate_monitoring_R
            ],
            wait_delay=1)
    start_service_data_transfer_BD.configure(scenario_service_data_transfer_BD)

    # service_data_transfer A -> C, first
    scenario_service_data_transfer_AC = service_data_transfer.build(
            server_entity=endpointC,
            client_entity=endpointA,
            server_ip=endpointC_ip,
            server_port=server_port,
            duration=None,
            file_size=AC_file_size, #10M
            tos=0,
            mtu=1400,
            scenario_name='service_data_transfer_AC')
    start_service_data_transfer_AC_1 = scenario.add_function(
            'start_scenario_instance',
            wait_launched=[start_service_data_transfer_BD],
            wait_delay=5)
    start_service_data_transfer_AC_1.configure(scenario_service_data_transfer_AC)

    # service_data_transfer A -> C, 2 to 10
    start_service_data_transfer_AC_2 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_1])
    start_service_data_transfer_AC_2.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_3 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_2])
    start_service_data_transfer_AC_3.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_4 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_3])
    start_service_data_transfer_AC_4.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_5 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_4])
    start_service_data_transfer_AC_5.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_6 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_5])
    start_service_data_transfer_AC_6.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_7 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_6])
    start_service_data_transfer_AC_7.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_8 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_7])
    start_service_data_transfer_AC_8.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_9 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_8])
    start_service_data_transfer_AC_9.configure(scenario_service_data_transfer_AC)

    start_service_data_transfer_AC_10 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_9])
    start_service_data_transfer_AC_10.configure(scenario_service_data_transfer_AC)

    # stop service_data_transfer B -> D
    stop_service_data_transfer_BD = scenario.add_function(
            'stop_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_10])
    stop_service_data_transfer_BD.configure(start_service_data_transfer_BD)

    ########################################
    ######## network_configure_link ########
    ########################################

    # network_configure_link L -> R t=0+10s
    scenario_network_conf_link_LR_10 = network_configure_link.build(
            entity=routerL,
            ifaces=interface_LR, #'ens4'
            mode='egress',
            operation='apply',
            bandwidth=bandwidth[1], #10M
            delay=delay[1], #10
            loss_model_params=loss[1], #0
            scenario_name='network_configure_link_LR_10')
    start_network_conf_link_LR_10 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_1],
            wait_delay=wait_delay_LR[0]) #10
    start_network_conf_link_LR_10.configure(scenario_network_conf_link_LR_10)

    # network_configure_link R -> L t=0+10s
    scenario_network_conf_link_RL_10 = network_configure_link.build(
            entity=routerR,
            ifaces=interface_RL, #'ens5'
            mode='egress',
            operation='apply',
            bandwidth=bandwidth[1], #10M
            delay=delay[1], #10
            loss_model_params=loss[1], #0
            scenario_name='network_configure_link_RL_10')
    start_network_conf_link_RL_10 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_service_data_transfer_AC_1],
            wait_delay=wait_delay_LR[0]) #10
    start_network_conf_link_RL_10.configure(scenario_network_conf_link_RL_10)

    # network_configure_link L -> R t=10+10s
    scenario_network_conf_link_LR_1010 = network_configure_link.build(
            entity=routerL,
            ifaces=interface_LR, #'ens4'
            mode='egress',
            operation='apply',
            bandwidth=bandwidth[2], #20M
            delay=delay[2], #10
            loss_model_params=loss[2], #0
            scenario_name='network_configure_link_LR_1010')
    start_network_conf_link_LR_1010 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_network_conf_link_LR_10, start_network_conf_link_RL_10],
            wait_delay=wait_delay_LR[1]) #10
    start_network_conf_link_LR_1010.configure(scenario_network_conf_link_LR_1010)

    # network_configure_link R -> L t=10+10s
    scenario_network_conf_link_RL_1010 = network_configure_link.build(
            entity=routerR,
            ifaces=interface_RL, #'ens5'
            mode='egress',
            operation='apply',
            bandwidth=bandwidth[2], #20M
            delay=delay[2], #10
            loss_model_params=loss[2], #0
            scenario_name='network_configure_link_RL_1010')
    start_network_conf_link_RL_1010 = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_network_conf_link_LR_10, start_network_conf_link_RL_10],
            wait_delay=wait_delay_LR[1]) #10
    start_network_conf_link_RL_1010.configure(scenario_network_conf_link_RL_1010)

    ########################################
    ################# pep ##################
    ########################################
    if pep:
        # We stop the pep jobs

        # stop pep job on RL
        stop_pep_RL = scenario.add_function(
                'stop_scenario_instance',
                wait_launched=[stop_service_data_transfer_BD])
        stop_pep_RL.configure(start_pep_RL)

        # stop pep job on LR
        stop_pep_LR = scenario.add_function(
                'stop_scenario_instance',
                wait_launched=[stop_service_data_transfer_BD])
        stop_pep_LR.configure(start_pep_LR)

    ########################################
    ########### rate_monitoring ############
    ########################################
    # We stop the rate_monitoring jobs

    # stop rate_monitoring job on C
    stop_rate_monitoring_C = scenario.add_function(
            'stop_scenario_instance',
            wait_launched=[stop_service_data_transfer_BD])
    stop_rate_monitoring_C.configure(start_rate_monitoring_C)

    # stop rate_monitoring job on D
    stop_rate_monitoring_D = scenario.add_function(
            'stop_scenario_instance',
            wait_launched=[stop_service_data_transfer_BD])
    stop_rate_monitoring_D.configure(start_rate_monitoring_D)

    # stop rate_monitoring job on R
    stop_rate_monitoring_R = scenario.add_function(
            'stop_scenario_instance',
            wait_launched=[stop_service_data_transfer_BD])
    stop_rate_monitoring_R.configure(start_rate_monitoring_R)

    ########################################
    ##### network_configure_link clear #####
    ########################################

    # network_configure_link L clear
    scenario_network_conf_link_L_clear = network_configure_link.build(
            entity=routerL,
            ifaces='{},{},{}'.format(interface_LA, interface_LB, interface_LR), #'ens3, ens6, ens4'
            mode='all',
            operation='clear',
            scenario_name='network_configure_link_L_clear')
    start_network_conf_link_L_clear = scenario.add_function(
            'start_scenario_instance',
            wait_launched=[
                stop_rate_monitoring_C,
                stop_rate_monitoring_D,
                stop_rate_monitoring_R
            ])
    start_network_conf_link_L_clear.configure(scenario_network_conf_link_L_clear)

    # network_configure_link R clear
    scenario_network_conf_link_R_clear = network_configure_link.build(
            entity=routerR,
            ifaces='{},{},{}'.format(interface_RC, interface_RD, interface_RL), #'ens6, ens3, ens5'
            mode='all',
            operation='clear',
            scenario_name='network_configure_link_R_clear')
    start_network_conf_link_R_clear = scenario.add_function(
            'start_scenario_instance',
            wait_launched=[
                stop_rate_monitoring_C,
                stop_rate_monitoring_D,
                stop_rate_monitoring_R
            ])
    start_network_conf_link_R_clear.configure(scenario_network_conf_link_R_clear)

    ########################################
    ########### post_processing ############
    ########################################

    if post_processing_entity is not None:
        wait_finished = [
                function
                for function in scenario.openbach_functions
                if isinstance(function, (StartJobInstance, StartScenarioInstance))
        ]

        for jobs, filters, legend, statistic, axis in [
                (['iperf3'], {'iperf3': iperf3_find_client}, _iperf3_legend, 'cwnd', 'cwnd (bytes)'),
                (['rate_monitoring'], {}, _rate_monitoring_legend, 'rate', 'rate (b/s)'),
        ]:
            post_processed = list(scenario.extract_function_id(*jobs, include_subscenarios=True, **filters))
            if post_processed:
                legends = [[legend(scenario.find_openbach_function(f))] for f in post_processed]
                title = axis.split(maxsplit=1)[0]

                time_series_on_same_graph(
                        scenario,
                        post_processing_entity,
                        post_processed,
                        [[statistic]],
                        [[axis]],
                        [['{} time series'.format(title)]],
                        legends,
                        wait_finished=wait_finished,
                        wait_delay=2)
                cdf_on_same_graph(
                        scenario,
                        post_processing_entity,
                        post_processed,
                        100,
                        [[statistic]],
                        [[axis]],
                        [['{} CDF'.format(title)]],
                        legends,
                        wait_finished=wait_finished,
                        wait_delay=2)

    return scenario
