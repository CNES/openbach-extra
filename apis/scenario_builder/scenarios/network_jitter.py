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
from scenario_builder.helpers.network.owamp import owamp_measure_owd
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance

SCENARIO_NAME = 'network_jitter'
SCENARIO_DESCRIPTION = """This scenario allows to retrieve
jitter information using owamp.
It can then, optionally, plot the jitter measurements using time-series and CDF.
"""

def jitter(
        server_entity, client_entity, server_ip,
        count, packets_interval, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('count', count)
    scenario.add_constant('packets_interval', packets_interval)

    owamp_measure_owd(
            scenario, client_entity, server_entity,
            '$server_ip', '$count', '$packets_interval')

    return scenario


def build(
        server_entity, client_entity, server_ip, count,
        packets_interval, post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = jitter(
            server_entity, client_entity, server_ip,
            count, packets_interval, scenario_name)

    if post_processing_entity is not None:
        waiting_jobs = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                waiting_jobs.append(function)
        post_processed = list(scenario.extract_function_id('owamp-client'))

        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['ipdv_sent', 'ipdv_received', 'pdv_sent', 'pdv_received']],
                [['Jitter (ms)']],
                [['Jitters time series']],
                [['owamp ipdv_sent'], ['owamp ipdv_received'], ['owamp pdv_sent'], ['owamp pdv_received']],
                False,
                waiting_jobs, None, 2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['ipdv_sent', 'ipdv_received', 'pdv_sent', 'pdv_received']],
                [['Jitter (ms)']],
                [['Jitters CDF']],
                [['owamp ipdv_sent'], ['owamp ipdv_received'], ['owamp pdv_sent'], ['owamp pdv_received']],
                False,
                waiting_jobs, None, 2)

    return scenario
