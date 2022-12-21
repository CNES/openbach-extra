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
from scenario_builder.helpers.service.ftp import ftp_multiple, ftp_single
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance

SCENARIO_NAME = 'service_ftp'
SCENARIO_DESCRIPTION = """This service_ftp scenario allows to :
 — Launch a ftp server;
 — Launch a ftp client;
 — Download or Upload a file, {}.

It can then, optionally, plot the throughput using time-series and CDF.
"""


def multiple_ftp(server_entity, client_entity, server_ip, server_port, mode, path, ftp_user, ftp_password, blocksize, amount, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format('multiple times'))
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('server_port', server_port)
    scenario.add_constant('mode', mode)
    scenario.add_constant('file_path', path)
    scenario.add_constant('ftp_user', ftp_user)
    scenario.add_constant('ftp_password', ftp_password)
    scenario.add_constant('blocksize', blocksize)

    ftp_multiple(
            scenario, client_entity, server_entity, '$server_ip', '$server_port', '$mode',
            '$file_path', amount, '$ftp_user', '$ftp_password', '$blocksize')

    return scenario


def single_ftp(server_entity, client_entity, server_ip, server_port, mode, path, ftp_user, ftp_password, blocksize, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format('once'))
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('server_port', server_port)
    scenario.add_constant('mode', mode)
    scenario.add_constant('file_path', path)
    scenario.add_constant('ftp_user', ftp_user)
    scenario.add_constant('ftp_password', ftp_password)
    scenario.add_constant('blocksize', blocksize)

    ftp_single(
            scenario, client_entity, server_entity, '$server_ip', '$server_port', '$mode',
            '$file_path', '$ftp_user', '$ftp_password', '$blocksize')

    return scenario


def build(
        server_entity, client_entity, server_ip, server_port, mode, file_path, multiple,
        ftp_user='openbach', ftp_password='openbach', blocksize='8192',
	    post_processing_entity=None, scenario_name=SCENARIO_NAME):
    # Create core scenario
    if mode == 'download':
        name_stat = 'throughput_sent'
        server_leg = 'sent'
        client_leg = 'received'
    elif mode == 'upload':
        name_stat = 'throughput_received'
        server_leg = 'received'
        client_leg = 'sent'
    else :
        raise ValueError('Mode must be "upload" or "download"')

    if multiple > 1:
        legend = [['Server throughput {}'.format(server_leg)]] + [
                ['Client_{} throughput {}'.format(n+1, client_leg)] for n in range(multiple)
        ]
        scenario = multiple_ftp(server_entity, client_entity, server_ip, server_port, mode, file_path, ftp_user, ftp_password, blocksize, multiple, scenario_name)
    elif multiple == 1:
        legend = [['Server throughput {}'.format(server_leg)], ['Client throughput {}'.format(client_leg)]]
        scenario = single_ftp(server_entity, client_entity, server_ip, server_port, mode, file_path, ftp_user, ftp_password, blocksize, scenario_name)
    else :
        raise ValueError("Multiple must be > 0")

    if post_processing_entity is not None:
        waiting_jobs = []
        for function in scenario.openbach_functions:
            if isinstance(function, StartJobInstance):
                waiting_jobs.append(function)

        post_processed = list(scenario.extract_function_id('ftp_clt', 'ftp_srv'))
        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['throughput_' + mode, name_stat]],
                [['Throughput (b/s)']],
                [[mode + ' throughput']],
                legend,
                wait_finished=waiting_jobs,
                wait_delay=2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['throughput_' + mode, name_stat]],
                [['Throughput (b/s)']],
                [[mode + ' throughput']],
                legend,
                wait_finished=waiting_jobs,
                wait_delay=2)

    return scenario
