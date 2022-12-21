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
from scenario_builder.helpers.service.quic import quic
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph


SCENARIO_NAME="""service_quic"""
SCENARIO_DESCRIPTION="""This *service_quic* scenario launches a server then a
client quic to download resources and post-processes collected data"""



def build(server_entity, server_ip, server_port, server_implementation, 
          client_entity, client_implementation, resources, nb_runs, 
          download_dir=None, server_log_dir=None, server_extra_args=None, client_log_dir=None, 
          client_extra_args=None, post_processing_entity=None, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    quic(scenario, 
         server_entity, server_ip, server_port, server_implementation, 
         client_entity, client_implementation, resources, nb_runs, 
         download_dir, server_log_dir, server_extra_args, client_log_dir, client_extra_args)

    if post_processing_entity:
       post_processed = list(scenario.extract_function_id('quic'))
       legends = []
       wait_finished = [function for function in scenario.openbach_functions if isinstance(function, StartJobInstance)]

       time_series_on_same_graph(
               scenario, 
               post_processing_entity, 
               post_processed, 
               [['download_time']], 
               [['DLT (ms)']], 
               [['DLT time series']], 
               [legends], 
               no_suffix=False,
               wait_finished=wait_finished, 
               wait_delay=5)
       cdf_on_same_graph(
               scenario, 
               post_processing_entity, 
               post_processed, 
               100, 
               [['download_time']], 
               [['DLT (ms)']], 
               [['DLT CDF']], 
               [legends],
               no_suffix=False, 
               wait_finished=wait_finished, 
               wait_delay=5)

    return scenario
