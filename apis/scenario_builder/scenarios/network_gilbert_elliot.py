#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2020 CNES
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

from scenario_builder.helpers.admin.pull_file import pull_file
from scenario_builder.helpers.admin.push_file import push_file

from scenario_builder.helpers.postprocessing.pcap_postprocessing import pcap_postprocessing_gilbert_elliot
from scenario_builder.helpers.transport.iperf3 import iperf3_rate_udp

SCENARIO_NAME = 'network_gilbert_elliot'
SCENARIO_DESCRIPTION = """This scenario allow to compute Gilbert Elliot parameters.
"""
# TODO update description

# TODO add src_ip, dst_ip, src_port, dst_port, proto

# TODO command PYTHONPATH=/home/bastien/Documents/OpenBACH/openbach-extra/apis/ python3 executor_network_gilbert_elliot.py --server-entity server --client-entity client --server-interface ens4 --client-interface ens4 --post-processing-entity server tests_iperf3 run


def gilbert_elliot(server_entity, client_entity, server_interface, client_interface, duration, scenario_name=SCENARIO_NAME):
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

    # TODO not en dur
    iperf3 = iperf3_rate_udp(scenario, client_entity, server_entity,
        "192.168.1.1", 5201, 1, "$duration", 0, "100k", 25,
        wait_launched=tcpdump_jobs, wait_delay=2)

    stopper = scenario.add_function(
            "stop_job_instance",
            wait_finished=iperf3,
            wait_delay=5)
    stopper.configure(*tcpdump_jobs)

    post_process = list(scenario.extract_function_id('tcpdump_pcap'))

    pull = pull_file(scenario, client_entity, ["/tmp/tcpdump_ge_client.pcap"], controller_path=["tcpdump_ge_client.pcap"],
            wait_finished=tcpdump_jobs, wait_launched=None, wait_delay=5)

    push = push_file(scenario, server_entity, ["/tmp/tcpdump_ge_client.pcap"], controller_path=["tcpdump_ge_client.pcap"],
            removes=[True], wait_finished=tcpdump_jobs, wait_launched=None, wait_delay=35)

    pcap_postprocessing_gilbert_elliot(scenario, server_entity, "/tmp/tcpdump_ge_server.pcap", "/tmp/tcpdump_ge_client.pcap",
            proto="udp", wait_finished=tcpdump_jobs, wait_delay=65)

    # TODO wait_finished use pull and push

    return scenario

def pcap_postprocessing(
        scenario, entity, capture_file, src_ip=None, dst_ip=None, 
        src_port=None, dst_port=None, proto=None, metrics_interval=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    f_start_analyze = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            capture_file=capture_file,        
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            proto=proto,
            metrics_interval=metrics_interval)

    f_start_analyze.configure(
            'pcap_postprocessing', entity, **parameters)

    return [f_start_analyze]



def build(
        server_entity, client_entity, server_interface, client_interface, duration,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = gilbert_elliot(server_entity, client_entity, server_interface, client_interface, duration, scenario_name)

    return scenario
