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
from scenario_builder.helpers.transport.iperf3 import iperf3_rate_tcp, iperf3_find_server
from scenario_builder.helpers.transport.nuttcp import nuttcp_rate_tcp, nuttcp_rate_udp, nuttcp_find_client
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance


SCENARIO_NAME = 'network_rate'
SCENARIO_DESCRIPTION = """This network_rate scenario allows to:
 - Compare the TCP rate measurement of iperf3 and nuttcp jobs and the UDP rate of nuttcp.
 - Perform two post-processing tasks to compare the
   time-series and the CDF of the rate measurements.
 - NB : client and server entities/IPs/ports are in accordance
   with iperf3 logic in reverse mode (server = sender and client = receiver)
"""


def rate(
        server_entity, client_entity, server_ip,
        server_port, command_port, duration, rate_limit, num_flows,
        tos, mtu, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('server_port', server_port)
    scenario.add_constant('command_port', command_port)
    scenario.add_constant('rate_limit', rate_limit)
    scenario.add_constant('num_flows', num_flows)
    scenario.add_constant('tos', tos)
    scenario.add_constant('mtu', mtu)
    scenario.add_constant('duration', duration)

    wait = iperf3_rate_tcp(
            scenario, client_entity, server_entity, '$server_ip', '$server_port', '$duration', '$num_flows', '$tos', '$mtu')
    wait = nuttcp_rate_tcp(
            scenario, client_entity, server_entity, '$server_ip', '$server_port', '$command_port',
            '$duration', '$num_flows', '$tos', '$mtu', wait, None, 2)
    wait = nuttcp_rate_udp(
            scenario, client_entity, server_entity, '$server_ip', '$server_port', '$command_port', '$duration', '$rate_limit', wait, None, 2)

    return scenario


def build(
        server_entity, client_entity, server_ip,
        server_port, command_port, duration, rate_limit, num_flows, tos, mtu,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = rate(
            server_entity, client_entity, server_ip, server_port,
            command_port, duration, rate_limit, num_flows, tos, mtu, scenario_name)

    if post_processing_entity is not None:
        waiting_jobs = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                waiting_jobs.append(function)

        post_processed = list(scenario.extract_function_id(iperf3=iperf3_find_server, nuttcp=nuttcp_find_client))

        no_suffix = num_flows != '1'
        legend = [
                ['{} TCP flow with iperf3 ({} to {})'.format(num_flows, client_entity, server_entity)],
                ['{} TCP flows with nuttcp ({} to {})'.format(num_flows, client_entity, server_entity)],
                ['1 UDP flow with nuttcp ({} to {})'.format(client_entity, server_entity)],
        ]

        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['rate', 'throughput']],
                [['Rate (b/s)']], [['Rate time series']],
                legend,
                no_suffix,
                'time_series_rate_{}_to_{}'.format(client_entity, server_entity),
                wait_finished=waiting_jobs,
                wait_delay=2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['rate', 'throughput']],
                [['Rate (b/s)']], [['Rate CDF']],
                legend,
                no_suffix,
                'histogram_rate_{}_to_{}'.format(client_entity, server_entity),
                wait_finished=waiting_jobs,
                wait_delay=2)

    return scenario
