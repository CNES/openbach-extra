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

from scenario_builder import Scenario
from scenario_builder.helpers.transport.iperf3 import iperf3_rate_tcp
from scenario_builder.helpers.transport.nuttcp import nuttcp_rate_tcp, nuttcp_rate_udp
from scenario_builder.helpers.metrology.d_itg import ditg_rate, ditg_pcket_rate
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance



SCENARIO_DESCRIPTION="""This network_rate scenario allows to :
     - Launch the subscenario network_rate_core
       (allowing to compare the TCP rate measurement of iperf3, d-itg
       and nuttcp jobs and the UDP rate of nuttcp and d-itg).
     - Perform two postprocessing tasks to compare the
       time-series and the CDF of the rate measurements.
"""
SCENARIO_NAME="""network_rate"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'nuttcp':
                if 'client' in function.start_job_instance['nuttcp']:
                    yield function_id
            elif function.job_name == 'iperf3':
                if 'server' in function.start_job_instance['iperf3']:
                    yield function_id
            elif function.job_name == 'd-itg_send': 
                yield function_id

def network_rate_core(client, server, scenario_name='network_rate_core'):
    scenario = Scenario(scenario_name, 'Comparison of rate measurements with TCP and UDP flows, by means of iperf3/nuttcp')
    scenario.add_argument('ip_dst', 'The destination IP for the clients')
    scenario.add_argument('ip_snd', 'The sender IP of d-itg sender, to get stats')
    scenario.add_argument('port', 'The port of the server')
    scenario.add_argument('command_port', 'The port of nuttcp server for signalling')
    scenario.add_argument('duration', 'The duration of each test (sec.)')
    scenario.add_argument('num_flows', 'The number of parallel flows to launch')
    scenario.add_argument('tos', 'The type of service used')
    scenario.add_argument('mtu', 'The MTU sizes to test')
    scenario.add_argument('rate', 'The rate for the UDP tests and d-itg TCP test')

    wait = iperf3_rate_tcp(scenario, client, server, '$ip_dst', '$port', '$duration', '$num_flows', '$tos', '$mtu')
    wait = nuttcp_rate_tcp(scenario, client, server, '$ip_dst', '$port', '$command_port', '$duration', '$num_flows', '$tos', '$mtu', wait, None, 2)
    wait = ditg_pcket_rate(scenario, client, server, '$ip_dst', '$ip_snd', 'TCP', '/tmp/', 1000, '$mtu', 100000, '$duration', 'owdm', 50, wait, None, 2)
    wait = nuttcp_rate_udp(scenario, client, server, '$ip_dst', '$port', '$command_port', '$duration', '$rate', wait, None, 2)
    ditg_rate(scenario, client, server, '$ip_dst', '$ip_snd', 'UDP', '/tmp/', 1000, '$mtu', '$rate', '$duration', 'owdm', 50, wait, None, 2)
 
    return scenario


def build(client, server, ip_dst, ip_snd, port, command_port, duration, rate, num_flows, tos, mtu, post_processing_entity, scenario_name=SCENARIO_NAME):
    # Create scenario and subscenario core
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    start_scenario_core = scenario.add_function(
            'start_scenario_instance')
    scenario_core = network_rate_core(client, server)
    start_scenario_core.configure(
            scenario_core, ip_dst=ip_dst,
            ip_snd=ip_snd, port=port,
            command_port=command_port,
            duration=duration,
            num_flows=num_flows,
            tos=tos, mtu=mtu,
            rate=rate)

    #Post processing part
    if post_processing_entity is not None:
        post_processed = [
                [start_scenario_core, function_id]
                for function_id in extract_jobs_to_postprocess(scenario_core)
        ]
        time_series_on_same_graph(scenario, post_processing_entity, post_processed,
            [['bitrate receiver (bps)', 'rate', 'throughput']],
            [['Rate (b/s)']], [['Rate time series']],
            [['{} TCP flow with iperf3'.format(num_flows)], ['{} TCP flows with nuttcp'.format(num_flows)],
             ['1 TCP flows with d-itg'], ['1 UDP flow with nuttcp'], ['1 UDP flow with d-itg']],
            [start_scenario_core], None, 2, True)

        cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, 
            [['rate', 'throughput', 'bitrate receiver (bps)']], 
            [['Rate (b/s)']], [['Rate CDF']], 
            [['{} TCP flow with iperf3'.format(num_flows)], ['{} TCP flow with nuttcp'.format(num_flows)], 
             ['1 TCP flows with d-itg'],['1 UDP flow with nuttcp'], ['1 UDP flow with d-itg']], 
            [start_scenario_core], None, 2, True)
        
    return scenario
