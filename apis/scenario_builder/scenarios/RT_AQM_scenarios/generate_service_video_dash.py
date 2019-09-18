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
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph

SCENARIO_DESCRIPTION="""This scenario launches one DASH transfert"""
SCENARIO_NAME="""generate_service_video_dash"""


def build(post_processing_entity, args, scenario_name=SCENARIO_NAME):
    print("Loading:",scenario_name)

    # Create top network_global scenario
    scenario = Scenario(scenario_name + "_" + args[0], SCENARIO_DESCRIPTION)

    # launching traffic
    start_scenario = scenario.add_function('start_job_instance')
    start_scenario.configure(
            'dash client', args[3], offset=0,
             dst_ip=args[8], protocol=args[10], duration=int(args[4]))

    return scenario