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
from scenario_builder.helpers.network.d_itg import ditg_packet_rate
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.helpers.admin.synchronization import synchronization
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance

SCENARIO_NAME = 'network_packet_loss'
SCENARIO_DESCRIPTION = """This network_packet_loss scenario allows to
measure the Packet Loss Rate of a link in a single direction.
It can then, optionally, plot the packet loss measurements using time-series and CDF.
"""


def packet_loss(
        server_entity, client_entity, server_ip, client_ip, duration,
        packet_size, packet_rate, max_synchro_off=None,
        synchronization_timeout=60, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('client_ip', client_ip)
    scenario.add_constant('duration', duration)
    scenario.add_constant('packet_size', packet_size)
    scenario.add_constant('packet_rate', packet_rate)

    wait_finished = []
    if max_synchro_off is not None and max_synchro_off > 0.0:
        synchro_ntp_client = synchronization(
                scenario, client_entity,
                max_synchro_off,
                synchronization_timeout)
        synchro_ntp_server = synchronization(
                scenario, server_entity,
                max_synchro_off,
                synchronization_timeout)

        wait_finished = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                wait_finished.append(function)


    ditg = ditg_packet_rate(
            scenario, client_entity, server_entity,
            '$server_ip', '$client_ip', 'UDP', packet_rate='$packet_rate',
            packet_size='$packet_size', duration='$duration', meter='owdm',
            wait_finished=wait_finished)

    return scenario



def build(
        server_entity, client_entity, server_ip, client_ip, duration,
        packet_size, packet_rate, max_synchro_off=None, synchronization_timeout=60,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = packet_loss(
            server_entity, client_entity, server_ip, client_ip,
            duration, packet_size, packet_rate, max_synchro_off,
            synchronization_timeout, scenario_name)

    if post_processing_entity is not None:
        waiting_jobs = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                waiting_jobs.append(function)

        post_processed = list(scenario.extract_function_id('d-itg_send'))
        legend = [['PLR ({} to {})'.format(client_entity, server_entity)]]
        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['packetloss_rate_receiver']],
                [['Packet Loss Rate (%)']],
                [['Packet Loss Rate time series']],
                legend,
                filename='time_series_packetloss_{}_to_{}'.format(client_entity, server_entity),
                wait_finished=waiting_jobs,
                wait_delay=2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['packetloss_rate_receiver']],
                [['Packet Loss Rate (%)']],
                [['Packet Loss Rate CDF']],
                legend,
                filename='histogram_packetloss_{}_to_{}'.format(client_entity, server_entity),
                wait_finished=waiting_jobs,
                wait_delay=2)

    return scenario
