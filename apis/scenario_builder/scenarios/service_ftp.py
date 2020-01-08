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


SCENARIO_NAME = """service_ftp"""
SCENARIO_DESCRIPTION = """This service_ftp scenario allows to :
    - Launch a ftp server and a ftp client, to either download or upload
a file, only once or multiple time
    - Perform two postprocessing tasks to compare the time-series and the CDF 
of the throughput.
"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'ftp_clt':
                    yield function_id
            elif function.job_name == 'ftp_srv':
                    yield function_id

def service_m(client, server, multiple, scenario_name = 'service_ftp_multiple'):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_argument('server_ip', "Server's IP")
    scenario.add_argument('port', "Server's port")
    scenario.add_argument('mode', "Download or upload")
    scenario.add_argument('file_path', 'Path of the exchanged file')
    scenario.add_argument('user', 'FTP authorized user')
    scenario.add_argument('password', "FTP authorized user's password")
    scenario.add_argument('blocksize', "Blocksize sent or received of data crunch")
    ftp_multiple(scenario, client, server, '$server_ip', '$port', '$mode', 
        '$file_path', multiple, '$user', '$password', '$blocksize')
    return scenario
    
def service_s(client, server, scenario_name = 'service_ftp_single'):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_argument('server_ip', "Server's IP")
    scenario.add_argument('port', "Server's port")
    scenario.add_argument('mode', 'Download or upload')
    scenario.add_argument('file_path', 'Path of the exchanged file')
    scenario.add_argument('user', 'FTP authorized user')
    scenario.add_argument('password', "FTP authorized user's password")
    scenario.add_argument('blocksize', "Blocksize sent or received of data crunch")
    ftp_single(scenario, client, server, '$server_ip', '$port', '$mode', 
        '$file_path', '$user', '$password', '$blocksize')
    return scenario

def build(client, server, server_ip, port, mode, file_path, multiple,
        user = 'openbach', password = 'openbach', blocksize = '8192', 
	post_processing_entity = None, scenario_name = SCENARIO_NAME):
        
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    start_scenario_core = scenario.add_function('start_scenario_instance')
    if mode == 'download':
        name_stat = 'throughput_sent'
    else: 
        name_stat = 'throughput_received'


    if multiple > 1:
        legend = [["Server's throughput"]]
        for n in range(1, multiple + 1) :
            legend.append(["Client_" + str(n) + "' throughput"])
        scenario_core = service_m(client, server, multiple)
        start_scenario_core.configure(scenario_core, server_ip = server_ip, port = port,
            mode = mode, file_path = file_path, user = user, password = password, 
            blocksize = blocksize)
    elif multiple == 1 :
        legend = [["Server's throughput"], ["Client's throughput"]]
        scenario_core = service_s(client, server)
        start_scenario_core.configure(scenario_core, server_ip = server_ip, port = port,
            mode = mode, file_path = file_path, user = user, password = password, 
            blocksize = blocksize)
    else :
        raise ValueError("Number of transfered file needs to be > 0")

    #Post processing part
    if post_processing_entity is not None:
        post_processed = [
            [start_scenario_core, function_id]
            for function_id in extract_jobs_to_postprocess(scenario_core)
        ]
        time_series_on_same_graph(scenario, post_processing_entity, post_processed,
            [['throughput_' + mode, name_stat]], [['Throughput (b/s)']], [[mode + ' throughput']],
            legend, [start_scenario_core], None, 2)
        cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, 
            [['throughput_' + mode, name_stat]], [['Throughput (b/s)']], [[mode + ' throughput']],
            legend, [start_scenario_core], None, 2)

    return scenario

