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

from scenario_builder import Scenario
from scenario_builder.helpers.network.fping import fping_measure_rtt
from scenario_builder.helpers.metrology.d_itg import ditg_pcket_rate
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance

SCENARIO_NAME = 'network_delay'
SCENARIO_DESCRIPTION = """This network_delay scenario allows to
compare the RTT measurement of fping (ICMP) and d-itg (UDP). It
can be configured to start the traffic either simultaneously or
sequentially.
It can then, optionally, plot the delay measurements using time-series and CDF.
"""


def simultaneous_traffic(server_entity, client_entity, server_ip, client_ip, duration, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('client_ip', client_ip)
    scenario.add_constant('duration', duration)

    srv = ditg_pcket_rate(
            scenario, client_entity, server_entity,
            '$server_ip', '$client_ip', 'UDP', packet_rate=1,
            duration='$duration', meter='rttm')
    fping_measure_rtt(
            scenario, client_entity, '$server_ip', '$duration',
            wait_launched=srv, wait_delay=1)

    return scenario


def sequential_traffic(server_entity, client_entity, server_ip, client_ip, duration, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('client_ip', client_ip)
    scenario.add_constant('duration', duration)

    ditg = ditg_pcket_rate(
            scenario, client_entity, server_entity,
            '$server_ip', '$client_ip', 'UDP', packet_rate=1,
            duration='$duration', meter='rttm')
    fping_measure_rtt(
            scenario, client_entity, '$server_ip', '$duration',
            wait_finished=ditg)

    return scenario


def build(
        server_entity, client_entity, server_ip, client_ip,
         duration, simultaneous,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = (simultaneous_traffic if simultaneous else sequential_traffic)(
            server_entity, client_entity,
            server_ip, client_ip,
            duration, scenario_name)

    if post_processing_entity is not None:
        waiting_jobs = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                waiting_jobs.append(function)

        post_processed = list(scenario.extract_function_id('fping', 'd-itg_send'))
        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['rtt', 'rtt_sender']],
                [['RTT delay (ms)']],
                [['RTTs time series']],
                [['d-itg_send'], ['fping']],
                waiting_jobs, None, 2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['rtt', 'rtt_sender']],
                [['RTT delay (ms)']],
                [['RTT CDF']],
                [['d-itg_send'], ['fping']],
                waiting_jobs, None, 2)

    return scenario
