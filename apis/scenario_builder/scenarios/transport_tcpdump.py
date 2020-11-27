#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
from scenario_builder.helpers.transport.tcpdump import *
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph



SCENARIO_NAME = 'transport_tcpdump'
SCENARIO_DESCRIPTION = """This scenario allows to capture packets on a network 
interface and analyze them
"""


def tcpdump_scenario_capture(
        entity, iface, capture_file, src_ip=None, dst_ip=None, 
        src_port=None, dst_port=None, proto=None, duration=None, analyze=False, metrics_interval=None,
        scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    if analyze:
       tcpdump_capture_analyze(scenario, entity, iface, capture_file, src_ip, dst_ip, 
                               src_port, dst_port, proto, duration, metrics_interval)
    else:
       tcpdump_capture_only(scenario, entity, iface, capture_file, src_ip, 
                            dst_ip, src_port, dst_port, proto, duration)
    return scenario


def tcpdump_scenario_analyze(
        entity, capture_file, src_ip=None, dst_ip=None, src_port=None, 
        dst_port=None, proto=None, metrics_interval=None,
        scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    tcpdump_analyze(scenario, entity, capture_file, src_ip, dst_ip, src_port, 
                    dst_port, proto, metrics_interval)
    return scenario


def build(entity, mode, iface=None, capture_file=None, src_ip=None, dst_ip=None, 
          src_port=None, dst_port=None, proto=None, duration=None, capture_analyze=False, metrics_interval=None,
          post_processing_entity=None, scenario_name=SCENARIO_NAME):
    if mode == 'capture':
       scenario = tcpdump_scenario_capture(entity, iface, capture_file, src_ip, dst_ip, src_port, 
                               dst_port, proto, duration, capture_analyze, metrics_interval, 
                               scenario_name)
    else:
       scenario = tcpdump_scenario_analyze(entity, capture_file, src_ip, dst_ip, src_port, 
                               dst_port, proto, metrics_interval, 
                               scenario_name)
    if (mode == 'analyze' or capture_analyze) and post_processing_entity:
       post_processed = list(scenario.extract_function_id('tcpdump'))
       legends = []
       wait_finished = [function for function in scenario.openbach_functions if isinstance(function, StartJobInstance)]
       
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
              False,
              wait_finished, None, 5),
           cdf_on_same_graph(
              scenario, 
              post_processing_entity, 
              post_processed, 
              100, 
              [[stat_name]], 
              [[cdf_label]], 
              [[cdf_title]], 
              [legends],
              False, 
              wait_finished, None, 10)
 
    return scenario
