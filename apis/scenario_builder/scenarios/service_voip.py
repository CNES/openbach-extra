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
from scenario_builder.helpers.service.voip import voip
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph


SCENARIO_DESCRIPTION = """This scenario launches one voip transfer.

It can then, optionally, plot the Mean Opinion Score using time-series and CDF.
"""
SCENARIO_NAME = 'service_voip'


def _voip(source, destination, duration, source_ip, destination_ip, port, codec, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    voip(scenario, destination, source, source_ip, destination_ip, port, codec, duration)
    return scenario


def build(
        source, destination, duration,
        source_ip, destination_ip, port, codec,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = _voip(source, destination, duration, source_ip, destination_ip, port, codec, scenario_name)

    if post_processing_entity is not None:
        post_processed = list(scenario.extract_function_id('voip_qoe_src'))
        legends = ['voip from {} to {}'.format(source, destination)]
        jobs = [function for function in scenario.openbach_functions if isinstance(function, StartJobInstance)]

        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['instant_mos']],
                [['MOS']],
                [['MOS time series']],
                [legends],
                jobs, None, 5)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['instant_mos']],
                [['MOS']],
                [['MOS CDF']],
                [legends],
                jobs, None, 5)

    return scenario
