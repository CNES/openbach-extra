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
from scenario_builder.openbach_functions import StartJobInstance

from scenario_builder.helpers.network.ip_route import ip_route
from scenario_builder.helpers.network.rohc import rohc_add_pop
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph


SCENARIO_NAME = 'network_rohc'
SCENARIO_DESCRIPTION = """This scenario allows to create a ROHC tunnel
between 2 entities and collects compression/decompression statistics.
The tunnel can be bidirectional or unidirectional.
It can then, optionally, plot the header compression ratio metrics using time-series and CDF.
"""


def rohc_tunnel_bidirectional(
        server_entity, client_entity, server_int_ipv4, client_int_ipv4,
        server_ext_ipv4, client_ext_ipv4, server_ext_ipv6, client_ext_ipv6,
        server_tunnel_ipv4, client_tunnel_ipv4, server_tunnel_ipv6, client_tunnel_ipv6,
        cid_type='largecid', max_contexts=16, rohc_packet_size=1500, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_int_ipv4', server_int_ipv4)
    scenario.add_constant('client_int_ipv4', client_int_ipv4)
    scenario.add_constant('server_ext_ipv4', server_ext_ipv4)
    scenario.add_constant('client_ext_ipv4', client_ext_ipv4)
    scenario.add_constant('server_tunnel_ipv4', server_tunnel_ipv4)
    scenario.add_constant('client_tunnel_ipv4', client_tunnel_ipv4)
    scenario.add_constant('server_tunnel_ipv6', server_tunnel_ipv6)
    scenario.add_constant('client_tunnel_ipv6', client_tunnel_ipv6)
    scenario.add_constant('cid_type', cid_type)
    scenario.add_constant('max_contexts', max_contexts)
    scenario.add_constant('rohc_packet_size', rohc_packet_size)

    server_rohc = rohc_add_pop(
        scenario, server_entity, '$client_int_ipv4', '$server_int_ipv4',
        '$server_tunnel_ipv4', '$server_tunnel_ipv6',
        behavior='both',
        direction='bidirectional',
        cid_type='$cid_type', max_contexts='$max_contexts', rohc_packet_size='$rohc_packet_size')

    client_rohc = rohc_add_pop(
        scenario, client_entity, '$server_int_ipv4', '$client_int_ipv4',
        '$client_tunnel_ipv4', '$client_tunnel_ipv6',
        behavior='both',
        direction='bidirectional',
        cid_type='$cid_type', max_contexts='$max_contexts', rohc_packet_size='$rohc_packet_size')

    server_route_v4 = ip_route(scenario, server_entity, 'replace', '$client_ext_ipv4', device='rohc0', restore=True,
        wait_launched=server_rohc + client_rohc, wait_delay=5)
    client_route_v4 = ip_route(scenario, client_entity, 'replace', '$server_ext_ipv4', device='rohc0', restore=True,
        wait_launched=server_rohc + client_rohc, wait_delay=5)

    if server_ext_ipv6 and client_ext_ipv6:
        scenario.add_constant('server_ext_ipv6', server_ext_ipv6)
        scenario.add_constant('client_ext_ipv6', client_ext_ipv6)
        server_route_v6 = ip_route(scenario, server_entity, 'replace', '$client_ext_ipv6', device='rohc0', restore=True,
            wait_launched=server_rohc + client_rohc, wait_delay=5)
        client_route_v6 = ip_route(scenario, client_entity, 'replace', '$server_ext_ipv6', device='rohc0', restore=True,
            wait_launched=server_rohc + client_rohc, wait_delay=5)

    return scenario


def rohc_tunnel_unidirectional(
        server_entity, client_entity, server_int_ipv4, client_int_ipv4,
        server_ext_ipv4, client_ext_ipv4, server_ext_ipv6, client_ext_ipv6,
        server_tunnel_ipv4, client_tunnel_ipv4, server_tunnel_ipv6, client_tunnel_ipv6,
        cid_type='largecid', max_contexts=16, rohc_packet_size=1500, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_int_ipv4', server_int_ipv4)
    scenario.add_constant('client_int_ipv4', client_int_ipv4)
    scenario.add_constant('server_ext_ipv4', server_ext_ipv4)
    scenario.add_constant('client_ext_ipv4', client_ext_ipv4)
    scenario.add_constant('server_tunnel_ipv4', server_tunnel_ipv4)
    scenario.add_constant('client_tunnel_ipv4', client_tunnel_ipv4)
    scenario.add_constant('server_tunnel_ipv6', server_tunnel_ipv6)
    scenario.add_constant('client_tunnel_ipv6', client_tunnel_ipv6)
    scenario.add_constant('cid_type', cid_type)
    scenario.add_constant('max_contexts', max_contexts)
    scenario.add_constant('rohc_packet_size', rohc_packet_size)

    server_rohc = rohc_add_pop(
        scenario, server_entity, '$client_int_ipv4', '$server_int_ipv4',
        '$server_tunnel_ipv4', '$server_tunnel_ipv6',
        behavior='send',
        direction = 'unidirectional',
        cid_type='$cid_type', max_contexts='$max_contexts', rohc_packet_size='$rohc_packet_size')

    client_rohc = rohc_add_pop(
        scenario, client_entity, '$server_int_ipv4', '$client_int_ipv4',
        '$client_tunnel_ipv4', '$client_tunnel_ipv6',
        behavior='receive',
        direction='unidirectional',
        cid_type='$cid_type', max_contexts='$max_contexts', rohc_packet_size='$rohc_packet_size')

    server_route_v4 = ip_route(scenario, server_entity, 'replace', '$client_ext_ipv4', device='rohc0', restore=True,
        wait_launched=server_rohc + client_rohc, wait_delay=5)
    client_route_v4 = ip_route(scenario, client_entity, 'replace', '$server_ext_ipv4', device='rohc0', restore=True,
        wait_launched=server_rohc + client_rohc, wait_delay=5)
    
    if server_ext_ipv6 and client_ext_ipv6:
        scenario.add_constant('server_ext_ipv6', server_ext_ipv6)
        scenario.add_constant('client_ext_ipv6', client_ext_ipv6)
        server_route_v6 = ip_route(scenario, server_entity, 'replace', '$client_ext_ipv6', device='rohc0', restore=True,
            wait_launched=server_rohc + client_rohc, wait_delay=5)
        client_route_v6 = ip_route(scenario, client_entity, 'replace', '$server_ext_ipv6', device='rohc0', restore=True,
            wait_launched=server_rohc + client_rohc, wait_delay=5)

    return scenario


def build(
        server_entity, client_entity, server_int_ipv4, client_int_ipv4,
        server_ext_ipv4, client_ext_ipv4, server_ext_ipv6, client_ext_ipv6,
        server_tunnel_ipv4, client_tunnel_ipv4, server_tunnel_ipv6, client_tunnel_ipv6,
        direction, cid_type, max_contexts, rohc_packet_size, duration=0,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):

    if direction == 'bidirectional':
        scenario = rohc_tunnel_bidirectional(
                server_entity, client_entity, server_int_ipv4, client_int_ipv4,
                server_ext_ipv4, client_ext_ipv4, server_ext_ipv6, client_ext_ipv6,
                server_tunnel_ipv4, client_tunnel_ipv4, server_tunnel_ipv6, client_tunnel_ipv6,
                cid_type, max_contexts, rohc_packet_size, scenario_name)

    if direction == 'unidirectional':
        scenario = rohc_tunnel_unidirectional(
                server_entity, client_entity, server_int_ipv4, client_int_ipv4,
                server_ext_ipv4, client_ext_ipv4, server_ext_ipv6, client_ext_ipv6,
                server_tunnel_ipv4, client_tunnel_ipv4, server_tunnel_ipv6, client_tunnel_ipv6,
                cid_type, max_contexts, rohc_packet_size, scenario_name)

    if duration:
        jobs = [f for f in scenario.openbach_functions if isinstance(f, StartJobInstance)]
        scenario.add_function('stop_job_instance', wait_launched=jobs, wait_delay=duration).configure(*jobs)

    if post_processing_entity is not None:
        waiting_jobs = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                waiting_jobs.append(function)

        post_processed = list(scenario.extract_function_id('rohc'))

        legend = [[server_entity], [client_entity]]

        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['comp_header_ratio']],
                [['Ratio']], [['Header Compression Ratio']],
                legend,
                filename='time_series_rohc_comp_header_ratio_{}_{}'.format(server_entity, client_entity),
                wait_finished=waiting_jobs,
                wait_delay=2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['comp_header_ratio']],
                [['Ratio']], [['Header Compression Ratio']],
                legend,
                filename='histogram_rohc_comp_header_ratio_{}_{}'.format(server_entity, client_entity),
                wait_finished=waiting_jobs,
                wait_delay=2)

    return scenario
