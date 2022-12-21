#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from scenario_builder.helpers.network.owamp import owamp_measure_owd
from scenario_builder.helpers.network.d_itg import ditg_packet_rate
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.helpers.admin.synchronization import synchronization
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance

SCENARIO_NAME = 'network_one_way_delay'
SCENARIO_DESCRIPTION = """This scenario allows to :
 - Launch One Way Delay measurement for both directions
   (with owamp jobs).
 - Perform two post-processing tasks to compare the
   time-series and the CDF of the one way delay measurements.
"""


def one_way_delay(
        server_entity, client_entity, server_ip, client_ip, count, packets_interval,
        max_synchro_off=None, synchronization_timeout=60, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('client_ip', client_ip)
    scenario.add_constant('count', count)
    scenario.add_constant('packets_interval', packets_interval)

    wait_finished = []
    if max_synchro_off is not None and max_synchro_off > 0.0:
        synchro_ntp_client = synchronization(
                scenario, client_entity, max_synchro_off,
                synchronization_timeout)
        synchro_ntp_server = synchronization(
                scenario, server_entity, max_synchro_off,
                synchronization_timeout)
        wait_finished = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                wait_finished.append(function)


    owamp_measure_owd(
            scenario, client_entity, server_entity,
            '$server_ip', '$count', '$packets_interval',
            wait_finished=wait_finished)
    ditg_packet_rate(
            scenario, client_entity, server_entity,
            '$server_ip', '$client_ip', 'UDP', packet_rate=1,
            wait_finished=wait_finished)

    return scenario


def build(
        server_entity, client_entity, server_ip, client_ip, count, 
        packets_interval, max_synchro_off=None, synchronization_timeout=60,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = one_way_delay(
            server_entity, client_entity,
            server_ip, client_ip, count,
            packets_interval, max_synchro_off,
            synchronization_timeout, scenario_name)

    if post_processing_entity is not None:
        waiting_jobs = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                waiting_jobs.append(function)

        post_processed = list(scenario.extract_function_id('owamp-client', 'd-itg_send'))
        legend = [
                ['Owamp OWD ({} to {})'.format(server_entity, client_entity)],
                ['Owamp OWD ({} to {})'.format(client_entity, server_entity)],
                ['D-ITG OWD ({} to {})'.format(client_entity, server_entity)],
                ['D-ITG OWD ({} to {})'.format(server_entity, client_entity)]
        ]
        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['owd_sent','owd_received', 'owd_receiver', 'owd_return']],
                [['One Way Delay (ms)']], [['Both One Way delays time series']],
                legend,
                filename='time_series_owd_{}_{}'.format(client_entity, server_entity),
                wait_finished=waiting_jobs,
                wait_delay=2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['owd_sent','owd_received', 'owd_receiver', 'owd_return']],
                [['One Way Delay (ms)']], [['Both One Way delay CDF']],
                legend,
                filename='histogram_owd_{}_{}'.format(client_entity, server_entity),
                wait_finished=waiting_jobs,
                wait_delay=2)

    return scenario
