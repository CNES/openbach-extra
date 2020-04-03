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
from scenario_builder.helpers.transport.iperf3 import iperf3_send_file_tcp, iperf3_find_server
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance


SCENARIO_DESCRIPTION = """This transport_tcp_one_flow scenario allows to:
 - Launch the subscenario transport_tcp_one_flow_core
   (Launch one tcp iperf3 flow with a transmitted size).
 - Perform two postprocessing tasks to compare the
   time-series and the CDF of the rate measurements.
"""
SCENARIO_NAME = 'transport_tcp_one_flow'


def tcp_one_flow(server_entity, client_entity, server_ip, server_port, size, tos, mtu, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('server_port', server_port)
    scenario.add_constant('transmitted_size', size)
    scenario.add_constant('tos', tos)
    scenario.add_constant('mtu', mtu)

    iperf3_send_file_tcp(scenario, client_entity, server_entity, '$server_ip', '$server_port', '$transmitted_size', '$tos', '$mtu')

    return scenario


def build(
        server_entity, client_entity, server_ip, server_port,
        transmitted_size, tos, mtu,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = tcp_one_flow(client_entity, server_entity, server_ip, server_port, transmitted_size, tos, mtu, scenario_name)

    if post_processing_entity is not None:
        waiting_jobs = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                waiting_jobs.append(function)

        post_processed = list(scenario.extract_function_id(iperf3=iperf3_find_server))
        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['throughput']],
                [['Rate (b/s)']],
                [['Rate time series']],
                [['iperf3']],
                waiting_jobs, None, 2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['throughput']],
                [['Rate (b/s)']],
                [['Rate CDF']],
                [['iperf3']],
                waiting_jobs, None, 2)

    return scenario
