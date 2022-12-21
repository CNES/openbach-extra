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
from scenario_builder.helpers.transport.tcpdump_pcap import tcpdump_pcap
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance
from scenario_builder.openbach_functions import StopJobInstance

SCENARIO_NAME = 'network_gilbert_elliott'
SCENARIO_DESCRIPTION = """This scenario allow to compute Gilbert Elliott parameters.
"""
# TODO update description

# TODO command PYTHONPATH=/home/bastien/Documents/OpenBACH/openbach-extra/apis/ python3 executor_network_gilbert_elliott.py --server-entity server --client-entity client --server-interface ens4 --client-interface ens4 --post-processing-entity server tests_iperf3 run

# TODO how many t and l in Elliott ?

def gilbert_elliott(server_entity, client_entity, server_interface, client_interface, duration, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant("server_interface", server_interface)
    scenario.add_constant("client_interface", client_interface)
    scenario.add_constant("duration", duration)

    tcpdump_jobs = []
    tcpdump_jobs += tcpdump_pcap(
      scenario, server_entity, "/tmp/tcpdump_ge_server.pcap", interface="$server_interface",
      wait_finished=None, wait_launched=None, wait_delay=0)
    tcpdump_jobs += tcpdump_pcap(
      scenario, client_entity, "/tmp/tcpdump_ge_client.pcap", interface="$client_interface",
      wait_finished=None, wait_launched=None, wait_delay=0)

    stopper = scenario.add_function(
            "stop_job_instance",
            wait_launched=tcpdump_jobs,
            wait_delay="$duration")
    stopper.configure(*tcpdump_jobs)

    post_process = list(scenario.extract_function_id('tcpdump_pcap'))

    # TODO add helper
    gather_files = scenario.add_function(
            "start_job_instance",
            wait_finished=tcpdump_jobs,
            wait_delay=2)

    gather_files.configure("gather_file", server_entity, agent=client_entity,
            job=[[post_process[1]]], statistic="pcap_file", destination_folder="/tmp")

    return scenario



def build(
        server_entity, client_entity, server_interface, client_interface, duration,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = gilbert_elliott(server_entity, client_entity, server_interface, client_interface, duration, scenario_name)

    return scenario
