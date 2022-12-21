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

from scenario_builder.helpers.admin.pull_file import pull_file
from scenario_builder.helpers.admin.push_file import push_file

from scenario_builder.helpers.postprocessing.pcap_postprocessing import pcap_postprocessing_gilbert_elliot
from scenario_builder.helpers.transport.iperf3 import iperf3_rate_udp

SCENARIO_NAME = 'network_gilbert_elliot'
SCENARIO_DESCRIPTION = """This scenario allow to compute Gilbert Elliot parameters.
It launches iperf3 UDP traffic and computes p and r parameters depending on the repartition of losses measured.
The number of packets needs to be high enough to have pertinent results.
For very low probabilities or to increase precision, duration or bandwidth may be increased.
"""

def gilbert_elliot(server_entity, client_entity, server_ip, client_ip, server_interface, client_interface,
                   server_port, udp_bandwidth, packet_size, duration, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant("server_ip", server_ip)
    scenario.add_constant("client_ip", client_ip)
    scenario.add_constant("server_interface", server_interface)
    scenario.add_constant("client_interface", client_interface)
    scenario.add_constant("server_port", server_port)
    scenario.add_constant("udp_bandwidth", udp_bandwidth)
    scenario.add_constant("packet_size", packet_size)
    scenario.add_constant("duration", duration)

    tcpdump_jobs = []
    tcpdump_jobs += tcpdump_pcap(
      scenario, server_entity, "/tmp/tcpdump_ge_server.pcap", interface="$server_interface",
      wait_finished=None, wait_launched=None, wait_delay=0)
    tcpdump_jobs += tcpdump_pcap(
      scenario, client_entity, "/tmp/tcpdump_ge_client.pcap", interface="$client_interface",
      wait_finished=None, wait_launched=None, wait_delay=0)

    iperf3 = iperf3_rate_udp(scenario, client_entity, server_entity,
        "$server_ip", "$server_port", "$duration", 1, 0, "$udp_bandwidth", "$packet_size",
        wait_launched=tcpdump_jobs, wait_delay=2)

    stopper = scenario.add_function(
            "stop_job_instance",
            wait_finished=iperf3,
            wait_delay=5)
    stopper.configure(*tcpdump_jobs)

    scenario_pull = Scenario("pull_file_scenario", "Sub-scenario used to pull file in Gilbert Elliot scenario")
    start_scenario_pull = scenario.add_function('start_scenario_instance', wait_finished=tcpdump_jobs, wait_launched=None, wait_delay=5)
    start_scenario_pull.configure(scenario_pull)
    pull_file(scenario_pull, client_entity, ["/tmp/tcpdump_ge_client.pcap"], controller_path=["tcpdump_ge_client.pcap"],
            wait_finished=None, wait_launched=None, wait_delay=0)

    scenario_push = Scenario("push_file_scenario", "Sub-scenario used to push file in Gilbert Elliot scenario")
    start_scenario_push = scenario.add_function('start_scenario_instance', wait_finished=[start_scenario_pull], wait_launched=None, wait_delay=5)
    start_scenario_push.configure(scenario_push)
    pull = push_file(scenario_push, server_entity, ["/tmp/tcpdump_ge_client.pcap"], controller_path=["tcpdump_ge_client.pcap"],
            removes=[True], wait_finished=tcpdump_jobs, wait_launched=None, wait_delay=35)

    pcap_postprocessing_gilbert_elliot(scenario, server_entity, "/tmp/tcpdump_ge_server.pcap", "/tmp/tcpdump_ge_client.pcap",
            src_ip="$server_ip", dst_ip="$client_ip", src_port="$server_port", proto="udp", wait_finished=[start_scenario_push], wait_delay=5)

    return scenario

def build(
        server_entity, client_entity, server_ip, client_ip, server_interface, client_interface, server_port=5201,
        udp_bandwidth="100k", packet_size=25, duration=60,
        post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = gilbert_elliot(server_entity, client_entity, server_ip, client_ip, server_interface, client_interface,
                            server_port, udp_bandwidth, packet_size, duration, scenario_name)

    return scenario