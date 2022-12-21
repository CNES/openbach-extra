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


import shlex
from collections import namedtuple

from scenario_builder import Scenario
from scenario_builder.openbach_functions import StartJobInstance
from scenario_builder.openbach_functions import StartScenarioInstance
from scenario_builder.helpers.service.apache2 import apache2
from scenario_builder.helpers.transport.iperf3 import iperf3_find_server
from scenario_builder.scenarios import service_data_transfer, service_video_dash, service_web_browsing, service_voip
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph

SCENARIO_NAME = 'service_traffic_mix'
SCENARIO_DESCRIPTION = """This scenario launches various traffic generators
as subscenarios. Possible generators are:
 - VoIP
 - Web browsing
 - Dash video player
 - Data transfer
It can then, optionally,  post-processes the generated data by plotting time-series and CDF.
"""


_Arguments = namedtuple('Arguments', ('id', 'traffic', 'source', 'destination', 'duration', 'wait_launched', 'wait_finished', 'wait_delay', 'source_ip', 'destination_ip'))
VoipArguments = namedtuple('VoipArguments', _Arguments._fields + ('port', 'codec', 'synchro_offset', 'synchro_timeout'))
WebBrowsingArguments = namedtuple('WebBrowsingArguments', _Arguments._fields + ('run_count', 'parallel_runs', 'urls'))
DashArguments = namedtuple('DashArguments', _Arguments._fields + ('protocol', 'tornado_port'))
DataTransferArguments = namedtuple('DataTransferArguments', _Arguments._fields + ('port', 'size', 'tos', 'mtu'))


def _iperf3_legend(openbach_function):
    iperf3 = openbach_function.start_job_instance['iperf3']
    port = iperf3['port']
    address = iperf3['server']['bind']
    destination = openbach_function.start_job_instance['entity_name']
    return 'Data Transfer - {} {} {}'.format(destination, address, port)


def _dash_legend(openbach_function):
    dash = openbach_function.start_job_instance['dashjs_client']
    destination = openbach_function.start_job_instance['entity_name']
    port = dash['tornado_port']
    return 'Dash - {} {}'.format(destination, port)


def _web_browsing_legend(openbach_function):
    destination = openbach_function.start_job_instance['entity_name']
    return 'Web Browsing - {}'.format(destination)


def _voip_legend(openbach_function):
    voip = openbach_function.start_job_instance['voip_qoe_src']
    port = voip['starting_port']
    address = voip['dest_addr']
    destination = openbach_function.start_job_instance['entity_name']
    return 'VoIP - {} {} {}'.format(destination, address, port)


def traffic_mix(arguments, post_processing_entity, scenario_name=SCENARIO_NAME):
    scenario_mix = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    wait_finished = []
    apache_servers = {}
    map_scenarios = {}

    # Launching Apache2 servers first (via apache2 or dashjs_player_server job)
    start_servers = []
    for args in arguments:
        if args.traffic in ["dash", "web_browsing"] and args.source not in apache_servers:
            start_server = apache2(scenario_mix, args.source)[0]
            apache_servers[args.source] = start_server
            start_servers.append(start_server)

    # Creating and launching traffic scenarios
    for args in arguments:
        wait_launched_list = [map_scenarios[i] for i in args.wait_launched]
        wait_finished_list = [map_scenarios[i] for i in args.wait_finished]

        offset_delay = 0
        if not wait_launched_list and not wait_finished_list:
            wait_launched_list = start_servers
            if start_servers:
                offset_delay = 5

        if args.traffic == "data_transfer":
            scenario_name = '{}_{}'.format(service_data_transfer.SCENARIO_NAME, args.id)
            scenario = service_data_transfer.build(
                    args.source, args.destination, args.source_ip,
                    args.port, args.duration, args.size,
                    args.tos, args.mtu,
                    post_processing_entity, scenario_name)
        elif args.traffic == "dash":
            scenario_name = '{}_{}'.format(service_video_dash.SCENARIO_NAME, args.id)
            scenario = service_video_dash.build(
                    args.source, args.destination, args.source_ip,
                    args.duration, args.protocol, args.tornado_port, False,
                    post_processing_entity, scenario_name)
        elif args.traffic == "web_browsing":
            scenario_name = '{}_{}'.format(service_web_browsing.SCENARIO_NAME, args.id)
            scenario = service_web_browsing.build(
                    args.source, args.destination, args.duration,
                    args.run_count, args.parallel_runs, urls=args.urls,
                    post_processing_entity=post_processing_entity,
                    scenario_name=scenario_name)
        elif args.traffic == "voip":
            scenario_name = '{}_{}'.format(service_voip.SCENARIO_NAME, args.id)
            scenario = service_voip.build(
                    args.destination, args.source, args.destination_ip,
                    args.source_ip, args.port, args.duration,
                    args.codec, args.synchro_offset, args.synchro_timeout,
                    post_processing_entity, scenario_name)

        start_scenario = scenario_mix.add_function(
                'start_scenario_instance',
                wait_finished=wait_finished_list,
                wait_launched=wait_launched_list,
                wait_delay=args.wait_delay + offset_delay)
        start_scenario.configure(scenario)
        wait_finished += [start_scenario]
        map_scenarios[args.id] = start_scenario

    # Stopping all Apache2 servers
    for server_entity, scenario_server in apache_servers.items():
        stopper = scenario_mix.add_function(
                'stop_job_instance',
                wait_finished=wait_finished,
                wait_delay=5)
        stopper.configure(scenario_server)

    return scenario_mix


def build(arguments, post_processing_entity, scenario_name=SCENARIO_NAME):
    scenario = traffic_mix(arguments, post_processing_entity, scenario_name)

    if post_processing_entity is not None:
        wait_finished = [
                function
                for function in scenario.openbach_functions
                if isinstance(function, (StartJobInstance, StartScenarioInstance))
        ]

        for jobs, filters, legend, statistic, axis in [
                ([], {'iperf3': iperf3_find_server}, _iperf3_legend, 'throughput', 'Rate (b/s)'),
                (['dashjs_client'], {}, _dash_legend, 'bitrate', 'Rate (b/s)'),
                (['dashjs_client'], {}, _dash_legend, 'buffer_length', 'Buffer length (s)'),
                (['web_browsing_qoe'], {}, _web_browsing_legend, 'page_load_time', 'PLT (ms)'),
                (['voip_qoe_src'], {}, _voip_legend, 'instant_mos', 'MOS'),
        ]:
            post_processed = list(scenario.extract_function_id(*jobs, include_subscenarios=True, **filters))
            if post_processed:
                legends = [[legend(scenario.find_openbach_function(f))] for f in post_processed]
                title = axis.split(maxsplit=1)[0]

                time_series_on_same_graph(
                        scenario,
                        post_processing_entity,
                        post_processed,
                        [[statistic]],
                        [[axis]],
                        [['{} time series'.format(title)]],
                        legends,
                        wait_finished=wait_finished,
                        wait_delay=2)
                cdf_on_same_graph(
                        scenario,
                        post_processing_entity,
                        post_processed,
                        100,
                        [[statistic]],
                        [[axis]],
                        [['{} CDF'.format(title)]],
                        legends,
                        wait_finished=wait_finished,
                        wait_delay=2)

    return scenario
