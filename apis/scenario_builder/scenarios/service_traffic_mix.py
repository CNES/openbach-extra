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


import shlex
from collections import namedtuple

from scenario_builder import Scenario
from scenario_builder.openbach_functions import StartJobInstance
from scenario_builder.helpers.service.apache2 import apache2
from scenario_builder.helpers.transport.iperf3 import iperf3_find_server
from scenario_builder.scenarios import service_data_transfer, service_video_dash, service_web_browsing, service_voip
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph


SCENARIO_DESCRIPTION = """This scenario launches various traffic generators
as subscenarios. Possible generators are:
 - VoIP
 - Web browsing
 - Dash video player
 - Data transfer
"""
LAUNCHER_DESCRIPTION = SCENARIO_DESCRIPTION + """
It then post-processes the generated data by plotting time-series and CDF.
"""
SCENARIO_NAME = 'Traffic Mix'


_Arguments = namedtuple('Arguments', ('id', 'traffic', 'source', 'destination', 'duration', 'wait_launched', 'wait_finished', 'wait_delay', 'source_ip', 'destination_ip'))
VoipArguments = namedtuple('VoipArguments', _Arguments._fields + ('port', 'codec'))
WebBrowsingArguments = namedtuple('WebBrowsingArguments', _Arguments._fields + ('run_count', 'parallel_runs'))
DashArguments = namedtuple('DashArguments', _Arguments._fields + ('protocol',))
DataTransferArguments = namedtuple('DataTransferArguments', _Arguments._fields + ('port', 'size', 'tos', 'mtu'))
ARGUMENTS_PER_TRAFFIC = {
        'voip': VoipArguments,
        'web_browsing': WebBrowsingArguments,
        'dash': DashArguments,
        'data_transfer': DataTransferArguments,
}


def _parse_waited_ids(ids):
    if ids == "None":
        return []
    return list(map(int, ids.split('-')))


def _load_args(args_list):
    arguments = []
    id_explored = set()
    for line in args_list:
        line = line.strip()
        if line.startswith('#') or len(line) < 10:
            continue

        args = shlex.split(line)
        try:
            args_parser = ARGUMENTS_PER_TRAFFIC[args[1]]
        except KeyError:
            print("\033[91mWARNING:", "Unknown traffic type:", args[1], "... ignoring", "\033[0m")
            continue
        try:
            args = args_parser(*args)
        except TypeError:
            print("\033[91mWARNING:", "Wrong argument format,", len(args_parser._fields), "elements needed for", args[1], "traffic:", "\"" + " ".join(args) + "\"", "but got", len(args), "... ignoring", "\033[0m")

        try:
            ids = _parse_waited_ids(args.wait_launched) + _parse_waited_ids(args.wait_finished)
            if args.id in id_explored:
                print("\033[91mWARNING:", "Duplicated id:", " ".join(args), "... ignoring")
                continue
            int(args.duration)
            int(args.delay)
            for dependency in ids:
                if dependency not in id_explored:
                    print("\033[91mWARNING:", "This traffic depends on missing ones:", " ".join(args), "... ignoring", "\033[0m")
                    break
            else:
                arguments.append(args)
                id_explored.add(cur_id)
        except ValueError:
            print("\033[91mWARNING:", "Cannot parse this line:", line, "\033[0m")

    return arguments


def _iperf3_legend(openbach_function):
    iperf3 = openbach_function.start_job_instance['iperf3']
    port = iperf3['port']
    address = iperf3['server']['bind']
    destination = openbach_function.start_job_instance['entity_name']
    return 'Data Transfer — {} {} {}'.format(destination, address, port)


def _dash_legend(openbach_function):
    return 'Dash'


def _web_browsing_legend(openbach_function):
    destination = openbach_function.start_job_instance['entity_name']
    return 'Web Browsing — {}'.format(destination)


def _voip_legend(openbach_function):
    voip = openbach_function.start_job_instance['voip_qoe_src']
    port = voip['starting_port']
    address = voip['dest_addr']
    destination = openbach_function.start_job_instance['entity_name']
    return 'VoIP — {} {} {}'.format(destination, address, port)


def traffic_mix(arguments, scenario_name=SCENARIO_NAME):
    scenario_mix = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    list_wait_finished = []
    apache_servers = {}
    map_scenarios = {}

    # Launching Apache2 servers first (via apache2 or dash player&server job)
    start_servers = []
    for args in arguments:
        if args.traffic == "dash" and args.source not in apache_servers:
            start_server = scenario_mix.add_function('start_job_instance')
            start_server.configure('dash player&server', args.source, offset=0)
            apache_servers[args.source] = start_server
            start_servers.append(start_server)
    for args in arguments:
        if args.traffic == "web_browsing" and args.source not in apache_servers:
            start_server = apache2(scenario_mix, args.source)[0]
            apache_servers[args.source] = start_server
            start_servers.append(start_server)

    # Creating and launching traffic scenarios
    for args in arguments:
        wait_launched_list = [map_scenarios[i] for i in _parse_waited_ids(args.wait_launched)]
        wait_finished_list = [map_scenarios[i] for i in _parse_waited_ids(args.wait_finished)]

        offset_delay = 0
        if not wait_launched_list and not wait_finished_list:
            wait_launched_list = start_servers
            if start_servers:
                offset_delay = 5

        if args.traffic == "data_transfer":
            scenario = service_data_transfer.build(
                    args.source, args.destination, int(args.duration),
                    args.destination_ip, int(args.port), args.size,
                    int(args.tos), int(args.mtu),
                    post_processing_entity, 'Data Transfer ' + args.id)
        elif args.traffic == "dash":
            scenario = service_video_dash.build(
                    args.source, args.destination, int(args.duration),
                    args.destination_ip, args.protocol, False,
                    post_processing_entity, 'Dash player ' + args.id)
        elif args.traffic == "web_browsing":
            scenario = service_web_browsing.build(
                    args.source, args.destination, int(args.duration),
                    int(args.nb_runs), int(args.parallel_runs),
                    post_processing_entity=post_processing_entity,
                    scenario_name='Web browsing ' + args.id)
        elif args.traffic == "voip":
            scenario = service_voip.build(
                    args.source, args.destination, int(args.duration),
                    args.source_ip, args.destination_ip,
                    int(args.port), args.codec,
                    post_processing_entity, 'VoIP ' + args.id)

        start_scenario = scenario_mix.add_function(
                'start_scenario_instance',
                wait_finished=wait_finished_list,
                wait_launched=wait_launched_list,
                wait_delay=int(args.wait_delay) + offset_delay)
        start_scenario.configure(scenario)
        list_wait_finished += [start_scenario]
        map_scenarios[args.id] = start_scenario
        
    # Stopping all Apache2 servers
    for server_entity,scenario_server in apache_servers.items():
        stopper = scenario_mix.add_function('stop_job_instance',
                wait_finished=list_wait_finished, wait_delay=5)
        stopper.configure(scenario_server)

    return scenario_mix


def build(post_processing_entity, extra_args_traffic, scenario_name=SCENARIO_NAME):
    # Create top network_traffix_mix scenario
    try:
        with open(extra_args_traffic) as extra_args_file:
            arguments = _load_args(extra_args_file)
    except (OSError, IOError):
        print("\033[91mERROR:", "Cannot open args file, exiting", "\033[0m")
        return

    scenario = traffic_mix(arguments, scenario_name)
    if post_processing_entity is None:
        return scenario

    # Wrap into meta scenario
    scenario_launcher = Scenario(scenario_name + ' with post-processing', LAUNCHER_DESCRIPTION)
    start_scenario = scenario_launcher.add_function('start_scenario_instance')
    start_scenario.configure(scenario)

    # Post processing data
    for jobs, filters, legend, statistic, axis in [
            ([], {'iperf3': iperf3_find_server}, _iperf3_legend, 'throughput', 'Rate (b/s)'),
            (['dash player&server'], {}, _dash_legend, 'bitrate', 'Rate (b/s)'),
            (['web_browsing_qoe'], {}, _web_browsing_legend, 'page_load_time', 'PLT (ms)'),
            (['voip_qoe_src'], {}, _voip_legend, 'instant_mos', 'MOS'),
    ]:
        post_processed = list(scenario_launcher.extract_function_id(*jobs, include_subscenarios=True, **filters))
        if post_processed:
            legends = [legend(scenario_launcher.find_openbach_function(f)) for f in post_processed]
            title = axis.split(maxsplit=1)[0]
            time_series_on_same_graph(
                    senario_launcher,
                    post_processing_entity,
                    post_processed,
                    [[statistic]],
                    [[axis]],
                    [['{} time series'.format(title)]],
                    [legends],
                    [start_scenario], None, 2)
            cdf_on_same_graph(
                    scenario_launcher,
                    post_processing_entity,
                    post_processed,
                    100,
                    [[statistic]],
                    [[axis]],
                    [['{} CDF'.format(title)]],
                    [legends],
                    [start_scenario], None, 2)

    return scenario_launcher
