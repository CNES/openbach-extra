#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from scenario_builder.helpers.transport.iperf3 import iperf3_rate_udp
from scenario_builder.helpers.network.owamp import owamp_measure_owd
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance

SCENARIO_DESCRIPTION="""This scenario allows to :
     - Launch the subscenario network_jitter
       (allowing to get jitter information with iperf3, owamp and d-itg
       and nuttcp jobs).
     - Perform two postprocessing tasks to compare the
       time-series and the CDF of the jitter measurements.
"""
SCENARIO_NAME="""network_jitter"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'owamp-client':
                yield function_id
            elif function.job_name == 'iperf3':
                if 'server' in function.start_job_instance['iperf3']:
                    yield function_id



def network_jitter_core(server, client, scenario_name='network_jitter_core'):
    scenario = Scenario(scenario_name, 'Comparison of jitter measurements with iperf3, owamp')
    scenario.add_argument('ip_dst', 'The destination IP for the clients')
    scenario.add_argument('port', 'The port of the server')
    scenario.add_argument('num_flows', 'The number of parallel flows to launch')
    scenario.add_argument('duration', 'The duration of each test (sec.)')
    scenario.add_argument('tos','the Type of service used')
    scenario.add_argument('bandwidth','the bandwidth of the measurement')

    wait = iperf3_rate_udp(scenario, client, server, '$ip_dst', '$port', '$num_flows', '$duration', '$tos', '$bandwidth')
    wait = owamp_measure_owd(scenario, client, server, '$ip_dst', wait)

    return scenario

def build(client, server, ip_dst, port, duration, num_flows, tos, bandwidth, post_processing_entity, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario_core = network_jitter_core(server, client)

    start_scenario_core = scenario.add_function(
            'start_scenario_instance')
    start_scenario_core.configure(
            scenario_core,
            ip_dst=ip_dst,
            port=port,
            num_flows=num_flows,
            duration=duration,
            tos=tos,
            bandwidth=bandwidth)
    post_processed = [
            [start_scenario_core, function_id]
            for function_id in extract_jobs_to_postprocess(scenario_core)
    ]

    time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['jitter', 'ipdv_sent', 'ipdv_received', 'pdv_sent', 'pdv_received']], [['Jitter (ms)']], [['Jitters time series']], [start_scenario_core], None, 2)
    cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, [['jitter', 'ipdv_sent', 'ipdv_received', 'pdv_sent', 'pdv_received']], [['Jitter (ms)']], [['Jitter CDF']], [start_scenario_core], None, 2)

    return scenario
