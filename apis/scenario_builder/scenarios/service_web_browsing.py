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
from scenario_builder.helpers.service.apache2 import apache2
from scenario_builder.helpers.service.web_browsing_qoe import web_browsing_qoe
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph


SCENARIO_DESCRIPTION="""This scenario launches one web transfert"""
SCENARIO_NAME="""service_web_browsing"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'web_browsing_qoe':
                yield function_id


def build(post_processing_entity, args, launch_server=False, scenario_name=SCENARIO_NAME):
    print("Loading:",scenario_name)

    # Create top network_global scenario
    scenario = Scenario(scenario_name + "_" + args[0], SCENARIO_DESCRIPTION)

    if launch_server:
        # launching server
        start_server = apache2(scenario, args[2])

        # launching traffic
        start_scenario = web_browsing_qoe(scenario, args[3], args[10], args[11], int(args[4]), wait_launched=start_server, wait_delay=5)

        # stopping server
        stopper = scenario.add_function('stop_job_instance',
                wait_finished=start_scenario, wait_delay=5)
        stopper.configure(start_server[0])

    else:
        # launching traffic
        start_scenario = web_browsing_qoe(scenario, args[3], args[10], args[11], int(args[4]))

    # Post processing data
    if post_processing_entity:
        post_processed = []
        legends = []
        for function_id in extract_jobs_to_postprocess(scenario):
            post_processed.append([function_id])
            legends.append([])
        if post_processed:
            time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['page_load_time']], [['PLT (ms)']], [['PLT time series']], legends, start_scenario, None, 2)
            cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, [['page_load_time']], [['PLT (ms)']], [['PLT CDF']], legends, start_scenario, None, 2)

    return scenario