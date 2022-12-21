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
from scenario_builder.helpers.transport.tcpdump_pcap import tcpdump_pcap
from scenario_builder.helpers.postprocessing.pcap_postprocessing import pcap_postprocessing
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph



SCENARIO_NAME = 'transport_tcpdump'
SCENARIO_DESCRIPTION = """This scenario allows to capture packets on a network 
interface and analyze them
"""


def scenario_capture(
        entity, capture_file, interface, src_ip=None, dst_ip=None, 
        src_port=None, dst_port=None, proto=None, duration=None,
        scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    tcpdump_pcap(scenario, entity, capture_file, interface, src_ip, 
                            dst_ip, src_port, dst_port, proto, duration)
    return scenario


def scenario_analyze(
        entity, capture_file, src_ip=None, dst_ip=None, src_port=None, 
        dst_port=None, proto=None, metrics_interval=None,
        scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    pcap_postprocessing(scenario, entity, capture_file, src_ip, dst_ip, src_port, 
                    dst_port, proto, metrics_interval)
    return scenario


def scenario_capture_and_analyze(
        entity, capture_file, interface=None, src_ip=None, dst_ip=None,
        src_port=None, dst_port=None, proto=None, duration=None, metrics_interval=None,
        scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    capture = tcpdump_pcap(scenario, entity, capture_file, interface, src_ip, 
                            dst_ip, src_port, dst_port, proto, duration)

    pcap_postprocessing(scenario, entity, capture_file, src_ip, dst_ip, src_port, 
                    dst_port, proto, metrics_interval, wait_finished=capture, wait_delay=2)
    return scenario



def build(entity, mode, capture_file=None, interface=None, src_ip=None, dst_ip=None, 
          src_port=None, dst_port=None, proto=None, duration=None, metrics_interval=None,
          post_processing_entity=None, scenario_name=SCENARIO_NAME):
    if mode == 'capture':
        scenario = scenario_capture(entity, capture_file, interface, src_ip, dst_ip, src_port, 
                               dst_port, proto, duration, scenario_name)
    if mode == 'analyze':
        scenario = scenario_analyze(entity, capture_file, src_ip, dst_ip, src_port, 
                               dst_port, proto, metrics_interval, scenario_name)
    if mode == 'both':
        scenario = scenario_capture_and_analyze(entity, capture_file, interface, src_ip, dst_ip, src_port, 
                               dst_port, proto, duration, metrics_interval, scenario_name)

    if mode in ('analyze', 'both') and post_processing_entity is not None:
        waiting_jobs = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                waiting_jobs.append(function)
 
        post_processed = list(scenario.extract_function_id('pcap_postprocessing'))
        legends = []
        for stat_name, ts_label, ts_title, cdf_label, cdf_title in (
               ('bit_rate', 'Bit Rate (Kbps)', 'Bit Rate time series', 'Bit Rate (Kbps)', 'Bit Rate CDF'),
               ('bytes_count', 'Bytes count (B)', 'Bytes count time series', 'Bytes count (B)', 'Bytes count CDF')):
            time_series_on_same_graph(
               scenario, 
               post_processing_entity, 
               post_processed, 
               [[stat_name]], 
               [[ts_label]], 
               [[ts_title]], 
               [legends], 
               filename='time_series_{}_{}'.format(stat_name, entity),
               wait_finished=waiting_jobs,
               wait_delay=5)
            cdf_on_same_graph(
               scenario, 
               post_processing_entity, 
               post_processed, 
               100, 
               [[stat_name]], 
               [[cdf_label]], 
               [[cdf_title]], 
               [legends],
               filename='histogram_{}_{}'.format(stat_name, entity),
    	   wait_finished=waiting_jobs,
               wait_delay=10)
 
    return scenario
