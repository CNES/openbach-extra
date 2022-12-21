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
from scenario_builder.helpers.service.apache2 import apache2
from scenario_builder.helpers.service.web_browsing_qoe import web_browsing_qoe
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph


SCENARIO_NAME = 'service_web_browsing'
SCENARIO_DESCRIPTION = """This scenario launches one web transfer.
It can then, optionally, plot the page load time using time-series and CDF.
NB : the entities logic is the following :
    - server sends web content
    - client requests for and receives web content
"""


def web_browsing_and_server(
        server_entity, client_entity, duration,
        nb_runs, nb_parallel_runs,
        compression=True, proxy_address=None, proxy_port=None,
        urls=None, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    server = apache2(scenario, server_entity)
    traffic = web_browsing_qoe(
            scenario, client_entity, duration, nb_runs, nb_parallel_runs,
            not compression, proxy_address, proxy_port, urls, wait_launched=server, wait_delay=5)

    stopper = scenario.add_function('stop_job_instance', wait_finished=traffic, wait_delay=5)
    stopper.configure(server[0])

    return scenario


def web_browsing(
        client_entity, duration, nb_runs, nb_parallel_runs,
        compression=True, proxy_address=None, proxy_port=None,
        urls=None, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    web_browsing_qoe(
            scenario, client_entity, duration, nb_runs, nb_parallel_runs,
            not compression, proxy_address, proxy_port, urls)

    return scenario


def build(
        server_entity, client_entity, duration, nb_runs, nb_parallel_runs,
        compression=True, proxy_address=None, proxy_port=None, urls=None, launch_server=False,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    if launch_server:
        scenario = web_browsing_and_server(server_entity, client_entity, duration, nb_runs, nb_parallel_runs, compression, proxy_address, proxy_port, urls, scenario_name)
    else:
        scenario = web_browsing(client_entity, duration, nb_runs, nb_parallel_runs, compression, proxy_address, proxy_port, urls, scenario_name)

    if post_processing_entity is not None:
        post_processed = list(scenario.extract_function_id('web_browsing_qoe'))
        legends = []
        jobs = [function for function in scenario.openbach_functions if isinstance(function, StartJobInstance)]

        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['page_load_time']],
                [['PLT (ms)']],
                [['PLT time series']],
                [legends],
                wait_finished=jobs,
                wait_delay=5)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['page_load_time']],
                [['PLT (ms)']],
                [['PLT CDF']],
                [legends],
                wait_finished=jobs,
                wait_delay=5)

    return scenario
