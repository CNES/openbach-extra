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
from scenario_builder.helpers.service.ftp import ftp_multiple, ftp_single
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance


SCENARIO_DESCRIPTION = """This service_ftp scenario allows to :
 — Launch a ftp server;
 — Launch a ftp client;
 — Download or Upload a file, {}.
"""
LAUNCHER_DESCRIPTION = SCENARIO_DESCRIPTION + """
It then plot the throughput using time-series and CDF.
"""
SCENARIO_NAME = 'FTP'


def multiple_ftp(client, server, ip, port, mode, path, user, password, blocksize, amount, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format('multiple times'))
    scenario.add_constant('server_ip', ip)
    scenario.add_constant('port', port)
    scenario.add_constant('mode', mode)
    scenario.add_constant('file_path', path)
    scenario.add_constant('user', user)
    scenario.add_constant('password', password)
    scenario.add_constant('blocksize', blocksize)
    ftp_multiple(scenario, client, server, '$server_ip', '$port', '$mode', 
        '$file_path', amount, '$user', '$password', '$blocksize')
    return scenario


def single_ftp(client, server, ip, port, mode, path, user, password, blocksize, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format('once'))
    scenario.add_constant('server_ip', ip)
    scenario.add_constant('port', port)
    scenario.add_constant('mode', mode)
    scenario.add_constant('file_path', path)
    scenario.add_constant('user', user)
    scenario.add_constant('password', password)
    scenario.add_constant('blocksize', blocksize)
    ftp_single(scenario, client, server, '$server_ip', '$port', '$mode', 
        '$file_path', '$user', '$password', '$blocksize')
    return scenario


def build(
        client, server, server_ip, port, mode, file_path, multiple,
        user='openbach', password='openbach', blocksize='8192', 
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
        scenario = multiple_ftp(client, server, server_ip, port, mode, file_path, user, password, blocksize, multiple, scenario_name)
    elif multiple == 1:
        legend = [['Server throughput {}'.format(server_leg)], ['Client throughput {}'.format(client_leg)]]
        scenario = single_ftp(client, server, server_ip, port, mode, file_path, user, password, blocksize, scenario_name)
    else :
        raise ValueError("Multiple must be > 0")

    if post_processing_entity is None:
        return scenario

    # Wrap into meta scenario
    scenario_launcher = Scenario(scenario_name + ' with post-processing', LAUNCHER_DESCRIPTION)
    start_scenario = scenario_launcher.add_function('start_scenario_instance')
    start_scenario.configure(scenario)

    #Post processing part
    post_processed = [[start_scenario, id] for id in scenario.extract_function_id('ftp_clt', 'ftp_srv')]
    time_series_on_same_graph(
            scenario_launcher,
            post_processing_entity,
            post_processed,
            [['throughput_' + mode, name_stat]],
            [['Throughput (b/s)']],
            [[mode + ' throughput']],
            legend,
            [start_scenario_core], None, 2)
    cdf_on_same_graph(
            scenario_launcher,
            post_processing_entity,
            post_processed,
            100,
            [['throughput_' + mode, name_stat]],
            [['Throughput (b/s)']],
            [[mode + ' throughput']],
            legend,
            [start_scenario_core], None, 2)

    return scenario_launcher

