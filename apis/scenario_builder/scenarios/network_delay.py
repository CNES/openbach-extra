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
from scenario_builder.helpers.network.fping import fping_measure_rtt
from scenario_builder.helpers.metrology.d_itg import ditg_pcket_rate
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance


SCENARIO_DESCRIPTION="""This network_delay scenario allows to :
     - Launch the subscenarios delay_simultaneous or delay_sequential
       (allowing to compare the RTT measurement of fping (ICMP),
       d-itg (UDP) ).
     - Perform two postprocessing tasks to compare the
       time-series and the CDF of the delay measurements.
"""
SCENARIO_NAME="""network_delay"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'fping':
                yield function_id
            elif function.job_name == 'd-itg_send':
                yield function_id


def network_delay_simultaneous_core(clt_entity, srv_entity, scenario_name='network_delay_simultaneous_core'):
    scenario = Scenario(scenario_name, 'OpenBACH Network Delay Measurement: Comparison of two RTT measurements simultaneously')
    scenario.add_argument('srv_ip', 'Target of the pings and server IP address')
    scenario.add_argument('clt_ip', 'IP address of source of pings and packets')
    scenario.add_argument('duration', 'The duration of fping/d-itg tests')

    srv = ditg_pcket_rate(scenario, clt_entity, srv_entity, '$srv_ip', '$clt_ip', 'UDP', packet_rate = 1, duration = '$duration', meter = "rttm")
    fping_measure_rtt(scenario, clt_entity, '$srv_ip', '$duration', wait_launched = srv, wait_delay = 1)

    return scenario


def network_delay_sequential_core(clt_entity, srv_entity, scenario_name='network_delay_sequential_core'):
    scenario = Scenario(scenario_name, 'OpenBACH Network Delay Measurement: Comparison of two RTT measurements one after the other')
    scenario.add_argument('srv_ip', 'Target of the pings and server IP adress')
    scenario.add_argument('clt_ip', 'IP address of source of pings and packets')
    scenario.add_argument('duration', 'The duration of each fping/d-itg tests')

    wait = ditg_pcket_rate(scenario, clt_entity, srv_entity, '$srv_ip', '$clt_ip', 'UDP', packet_rate = 1, duration = '$duration', meter = "rttm")
    wait = fping_measure_rtt(scenario, clt_entity, '$srv_ip', '$duration', wait_finished = wait)

    return scenario


def build(clt_entity, srv_entity, clt_ip, srv_ip, duration, simultaneous, post_processing_entity, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    if simultaneous:
       scenario_core = network_delay_simultaneous_core(clt_entity, srv_entity)
    else:
       scenario_core = network_delay_sequential_core(clt_entity, srv_entity)

    start_scenario_core = scenario.add_function(
            'start_scenario_instance')

    start_scenario_core.configure(
            scenario_core,
            srv_ip=srv_ip,
            clt_ip=clt_ip,
            duration=duration)

    if post_processing_entity is not None:
       post_processed = [
            [start_scenario_core, function_id]
            for function_id in extract_jobs_to_postprocess(scenario_core)
       ]
       time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['rtt', 'rtt_sender']], [['RTT delay (ms)']], [['RTTs time series']], [['d-itg_send'], ['fping']], [start_scenario_core], None, 2)
       cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, [['rtt', 'rtt_sender']], [['RTT delay (ms)']], [['RTT CDF']], [['d-itg_send']['fping']], [start_scenario_core], None, 2)

    return scenario
