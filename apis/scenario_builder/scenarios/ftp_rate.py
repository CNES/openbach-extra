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


SCENARIO_DESCRIPTION = """This scenario allows to launch:
 — a FTP server;
 — and an associated client.
And transfer files between them.

It can then, optionally, plot the applicative rate using time-series and CDF.
"""
SCENARIO_NAME = 'ftp_rate'


def ftp_rate(client, server, ip_destination, port, command_port, duration, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('ip_destination', ip_destination)
    scenario.add_constant('port', port)
    scenario.add_constant('command_port', command_port)
    scenario.add_constant('duration', duration)

    wait = ftp_server(scenario, client, server, '$ip_destination', '$port')
    ftp_client(scenario, client, server, '$ip_destination', '$port', '$command_port', '$duration', wait, None, 5)

    return scenario


def build(
        client, server, ip_destination, port,
        command_port, duration, rate,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = ftp_rate(client, server, ip_destination, port, command_port, duration, scenario_name)

    if post_processing_entity is not None:
        post_processed = list(scenario.extract_function_id('ftp_server'))
        jobs = scenario.openbach_functions.copy()

        time_series_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                [['bitrate']],
                [['Rate (b/s)']],
                [['FTP Rate time series']],
                [['rate ftp']],
                jobs, None, 2)
        cdf_on_same_graph(
                scenario,
                post_processing_entity,
                post_processed,
                100,
                [['bitrate']],
                [['Rate (b/s)']],
                [['FTP Rate CDF']],
                [['Rate ftp']],
                jobs, None, 2)

    return scenario
