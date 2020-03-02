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
from scenario_builder.helpers.transport.iperf3 import iperf3_rate_udp, iperf3_find_server
from scenario_builder.helpers.network.owamp import owamp_measure_owd
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance


SCENARIO_DESCRIPTION = """This scenario allows to retrieve
jitter information using iperf3 and owamp.
"""
LAUNCHER_DESCRIPTION = SCENARIO_DESCRIPTION + """
It then plot the jitter measurements using time-series and CDF.
"""
SCENARIO_NAME = 'Network Jitter'


def jitter(
        client_entity, server_entity, server_ip, server_port,
        num_flows, duration, tos, bandwidth, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('srv_ip', server_ip)
    scenario.add_constant('srv_port', server_port)
    scenario.add_constant('num_flows', num_flows)
    scenario.add_constant('duration', duration)
    scenario.add_constant('tos', tos)
    scenario.add_constant('bandwidth', bandwidth)

    # Remove iperf3 jitter test ? Seems 0 when testing
    # Add d-itg if good jitter measure ?
    iperf = iperf3_rate_udp(
            scenario, client_entity, server_entity,
            '$srv_ip', '$srv_port', '$num_flows',
            '$duration', '$tos', '$bandwidth')
    owamp_measure_owd(scenario, clt_entity, srv_entity, '$srv_ip', iperf)

    return scenario


def build(clt_entity, srv_entity, srv_ip, srv_port, duration, num_flows, tos, bandwidth, post_processing_entity=None, scenario_name=SCENARIO_NAME):
    # Create core scenario
    scenario = jitter(clt_entity, srv_entity, srv_ip, srv_port, num_flows, duration, tos, bandwidth, scenario_name)
    if post_processing_entity is None:
        return scenario

    # Wrap into meta scenario
    scenario_launcher = Scenario(scenario_name + ' with post-processing', LAUNCHER_DESCRIPTION)
    start_scenario = scenario_launcher.add_function('start_scenario_instance')
    start_scenario.configure(scenario)

    # Add post-processing to meta scenario
    post_processed = [[start_scenario, id] for id in scenario.extract_function_id('owamp-client', iperf3=iperf3_find_server)]
    time_series_on_same_graph(
            scenario_launcher,
            post_processing_entity,
            post_processed,
            [['jitter', 'ipdv_sent', 'ipdv_received', 'pdv_sent', 'pdv_received']],
            [['Jitter (ms)']],
            [['Jitters time series']],
            [['iperf3 jitter'], ['owamp ipdv_sent'], ['owamp ipdv_received'], ['owamp pdv_send'], ['owamp pdv_received']],
            [start_scenario_core], None, 2)
    cdf_on_same_graph(
            scenario_launcher,
            post_processing_entity,
            post_processed,
            100,
            [['jitter', 'ipdv_sent', 'ipdv_received', 'pdv_sent', 'pdv_received']],
            [['Jitter (ms)']],
            [['Jitters CDF']],
            [['iperf3 jitter'], ['owamp ipdv_sent'], ['owamp ipdv_received'], ['owamp pdv_send'], ['owamp pdv_received']],
            [start_scenario_core], None, 2)

    return scenario
