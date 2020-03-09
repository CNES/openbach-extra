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
from scenario_builder.openbach_functions import StartJobInstance
from scenario_builder.helpers.transport.iperf3 import iperf3_send_file_tcp, iperf3_rate_tcp, iperf3_find_server
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph


SCENARIO_DESCRIPTION = """This scenario launches one iperf3 transfer.

It can then, optionally, plot the throughput using time-series and CDF.
"""
SCENARIO_NAME = 'service_data_transfer'


def data_transfer(source, destination, duration, ip, port, size, tos, mtu, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    if size == '0':
        iperf3_rate_tcp(scenario, source, destination, ip, port, duration, 1, tos, mtu)
    else:
        iperf3_send_file_tcp(scenario, source, destination, ip, port, size, tos, mtu)

    return scenario


def build(
        source, destination, duration, destination_ip, port, size, tos,
        mtu, post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = data_transfer(source, destination, duration, destination_ip, port, size, tos, mtu, scenario_name)

    if post_processing_entity is not None:
        post_processed = list(scenario.extract_function_id(iperf3=iperf3_find_server))
        jobs = [function for function in scenario.openbach_functions if isinstance(function, StartJobInstance)]
        legends = ['iperf3 from {} to {}, port {}'.format(source, destination, port)]

        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['throughput']],
                [['Rate (b/s)']],
                [['Rate time series']],
                [legends],
                jobs, None, 2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['throughput']],
                [['Rate (b/s)']],
                [['Rate CDF']],
                [legends],
                jobs, None, 2)

    return scenario
