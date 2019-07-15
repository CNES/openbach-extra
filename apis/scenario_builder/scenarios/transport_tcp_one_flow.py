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
from scenario_builder.helpers.transport.iperf3 import iperf3_send_file_tcp

from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance



SCENARIO_DESCRIPTION="""This transport_tcp_one_flow scenario allows to :
     - Launch the subscenario transport_tcp_one_flow_core
       (Launch one tcp iperf3 flow with a transmitted size).
     - Perform two postprocessing tasks to compare the
       time-series and the CDF of the rate measurements.
"""
SCENARIO_NAME="""transport_tcp_one_flow"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'iperf3':
                if 'server' in function.start_job_instance['iperf3']:
                    yield function_id

def transport_tcp_one_flow_core(client, server, scenario_name='transport_tcp_one_flow_core'):
    scenario = Scenario(scenario_name, 'Launch one tcp iperf3 flow with a transmitted size')
    scenario.add_argument('ip_dst', 'The destination IP for the clients')
    scenario.add_argument('port', 'The port of the server')
    scenario.add_argument('transmitted_size', 'The transmitted size of the one TCP iperf3 flow')
    scenario.add_argument('tos', 'The type of service used')
    scenario.add_argument('mtu', 'The MTU sizes to test')

    wait = iperf3_send_file_tcp(scenario, client, server, '$ip_dst', '$port', '$transmitted_size', '$tos', '$mtu')

    return scenario


def build(client, server, ip_dst, port, transmitted_size, tos, mtu, post_processing_entity, scenario_name=SCENARIO_NAME):
    # Create scenario and subscenario core
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    start_scenario_core = scenario.add_function(
            'start_scenario_instance')
    scenario_core = transport_tcp_one_flow_core(client, server)
    start_scenario_core.configure(
            scenario_core,
            ip_dst=ip_dst, port=port,
            transmitted_size=transmitted_size,
            tos=tos, mtu=mtu)

    #Post processing part
    if post_processing_entity is not None:
        post_processed = [
                [start_scenario_core, function_id]
                for function_id in extract_jobs_to_postprocess(scenario_core)
        ]
        time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['throughput']], [['Rate (b/s)']], [['Rate time series']], [['iperf3']], [start_scenario_core], None, 2)
        cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, [['throughput']], [['Rate (b/s)']], [['Rate CDF']], [['iperf3']], [start_scenario_core], None, 2)

    return scenario
