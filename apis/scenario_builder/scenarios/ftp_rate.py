#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
from scenario_builder.helpers.service.ftp import ftp
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance



SCENARIO_DESCRIPTION="""This rate_rate scenario allows to :
     - Launch the subscenario rate_ftp_ecore
       (allowing to launch a ftp server and a ftp client)
     - Perform two postprocessing tasks to measure the
       time-series and the CDF of the applicative rate.
"""
SCENARIO_NAME="""ftp_rate"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'ftp_server':
               yield function_id

def rate_ftp_core(client, server, scenario_name='rate_ftp_core'):
    scenario = Scenario(scenario_name, 'Measures the applicative rate of a FTP flow (transmissions of a file)')
    scenario.add_argument('ip_dst', 'The destination IP for the clients')
    scenario.add_argument('port', 'The port of the server')
    scenario.add_argument('command_port', 'The port of nuttcp server for signalling')
    scenario.add_argument('duration', 'The duration of each test (sec.)')

    wait = ftp_server(scenario, client, server, '$ip_dst', '$port')
    ftp_client(scenario, client, server, '$ip_dst', '$port', '$command_port', '$duration', wait, None, 5)

    return scenario


def build(client, server, ip_dst, port, command_port, duration, rate, post_processing_entity, scenario_name=SCENARIO_NAME):
    # Create scenario and subscenario core
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    start_scenario_core = scenario.add_function(
            'start_scenario_instance')
    scenario_core = rate_ftp_core(client, server)
    start_scenario_core.configure(
            scenario_core,
            ip_dst=ip_dst, port=port,
            command_port=command_port,
            duration=duration)

    #Post processing part
    if post_processing_entity is not None:
        post_processed = [
                [start_scenario_core, function_id]
                for function_id in extract_jobs_to_postprocess(scenario_core)
        ]
        time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['bitrate']], [['Rate (b/s)']], [['FTP Rate time series']], [['rate ftp']], [start_scenario_core], None, 2)
        cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, [['bitrate']], [['Rate (b/s)']], [['FTP Rate CDF']], [['Rate ftp']], [start_scenario_core], None, 2)

    return scenario
