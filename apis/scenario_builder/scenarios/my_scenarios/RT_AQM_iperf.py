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
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance



SCENARIO_DESCRIPTION="""This scenario allows to launch several UDP transmissions, 
    using iperf3, to several destinations and ports.
"""
SCENARIO_NAME="""RT_AQM_iperf"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'iperf3':
                if 'server' in function.start_job_instance['iperf3']:
                    port = function.start_job_instance['iperf3']['port']
                    address = function.start_job_instance['iperf3']['server']['bind']
                    yield (function_id, address, port)

def build(duration, post_processing_entity, args, scenario_id, scenario_name=SCENARIO_NAME):

    print(scenario_name + "_" + str(scenario_id))

    scenario = Scenario(scenario_name + "_" + scenario_id, SCENARIO_DESCRIPTION)
    src, dst, ip_dst, port, bandwidth, tos = args

    server = scenario.add_function('start_job_instance')
    server.configure(
            'iperf3', dst, offset=0,
            num_flows=1, port=port,
            interval=1.0, server={'exit':True, 'bind':ip_dst})

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', src, offset=0,
             num_flows=1, port=port,
             client={
                'server_ip': ip_dst,
                'duration_time': duration,
                'tos': '{0}'.format(tos),
                'udp': {'bandwidth':'{0}'.format(bandwidth)},
                })

    #Post processing part
    if post_processing_entity is not None:
        post_processed = []
        legends = []
        for function_id, address, port in extract_jobs_to_postprocess(scenario):
            post_processed.append([scenario, function_id])
            legends.append([address + " " + str(port)])
            print(post_processed[-1],legends[-1])
            #time_series_on_same_graph(scenario, post_processing_entity, [post_processed[-1]], [['throughput']], [['Rate (b/s)']], [['Rate time series']], [legends[-1]], [server], None, 2)

        #time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['throughput']], [['Rate (b/s)']], [['Rate time series']], legends, [server], None, 2)

    return scenario