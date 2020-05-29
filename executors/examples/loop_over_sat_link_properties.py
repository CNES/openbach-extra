#!/usr/bin/env python

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2019 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

"""Example of scenarios composition.

This would combine the capabilities of add_loss_inf and
data_download_configure_link examples but is shown in an
alternative way that may be more suitable for advanced
post-processing usages.
"""


from auditorium_scripts.scenario_observer import ScenarioObserver, DataProcessor
from scenario_builder import Scenario
from scenario_builder.helpers.transport.iperf3 import iperf3_find_server
from scenario_builder.scenarios.service_data_transfer import build as service_data_transfer
from scenario_builder.scenarios.network_configure_link import (
        configure_link_scenario_apply,
        configure_link_scenario_clear,
)

import pandas as pd
import matplotlib.pyplot as plt


def extract_iperf_statistic(job):
    data = job.statistics_data[('Flow1',)].dated_data
    timestamps = pd.Series(data.keys(), name=None)
    timestamps -= timestamps.min()
    return pd.DataFrame({'throughput': [stats['throughput'] for stats in data.values()]}, index=timestamps)


def setup(scenario, name, entity, interfaces, mode, bandwidth=None, delay=0, loss_model='random', loss_model_params=[0.0], wait_finished=None):
    sub = scenario.add_function('start_scenario_instance', wait_finished=wait_finished)
    sub.configure(configure_link_scenario_apply(entity, interfaces, mode, bandwidth, 'normal', delay, 0, loss_model, loss_model_params, 10000, name))
    return sub


def add_download_scenario(scenario, name, server, client, duration, ip, port, file_size, post_processing_entity, wait_finished=None):
    sub = scenario.add_function('start_scenario_instance', wait_finished=wait_finished)
    sub.configure(service_data_transfer(server, client, duration, ip, port, file_size, 0x04, 1400, post_processing_entity, name))
    return sub


def teardown(scenario, name, entity, interfaces, mode, wait_finished=None):
    sub = scenario.add_function('start_scenario_instance', wait_finished=wait_finished)
    sub.configure(configure_link_scenario_clear(entity, interfaces, mode, name))
    return sub


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--pep-entity', required=True,
            help='Name of the pep entity where configure link should run')
    observer.add_scenario_argument(
            '--pep-interfaces', required=True,
            help='Comma-separated list of the network interfaces to emulate link on on the pep')
    observer.add_scenario_argument(
            '--pep-bandwidth', default='300M',
            help='')
    observer.add_scenario_argument(
            '--pep-delay', default=1, type=int,
            help='')
    observer.add_scenario_argument(
            '--middlebox-entity', required=True,
            help='Name of the middlebox entity where configure link should run')
    observer.add_scenario_argument(
            '--middlebox-interfaces', required=True,
            help='Comma-separated list of the network interfaces to emulate link on on the middlebox')
    observer.add_scenario_argument(
            '--server', '--data-transfer-server', '-s', required=True,
            help='Name of the entity where the data transfer server should run')
    observer.add_scenario_argument(
            '--client', '--data-transfer-client', '-c', required=True,
            help='Name of the entity where the data transfer client should run')
    observer.add_scenario_argument(
            '--server-ip', '-I', required=True,
            help='IP of the server')
    observer.add_scenario_argument(
            '--client-ip', '-i', required=True,
            help='IP of the client')
    observer.add_scenario_argument(
            '--port', '-p', default=5201, type=int,
            help='Port used for the data transfer')
    observer.add_scenario_argument(
            '--post-processing-entity',
            help='Name of the entity where the post-processing jobs should run')
    observer.add_scenario_argument(
            '--file-size', '--size', '-f', default='500M',
            help='Size of the file transfer')
    observer.add_scenario_argument(
            '--duration', '-l', default=10, type=int,
            help='Duration of the file transfer')
    observer.add_scenario_argument(
            '--delay-server-to-client', '-D', default=325,
            help='Delay for a packet to go from the server to the client')
    observer.add_scenario_argument(
            '--delay-client-to-server', '-d', default=325,
            help='Delay for a packet to go from the client to the server')

    args = observer.parse(argv, 'Loop over satellite link properties')


    legends = []
    name = args.scenario_name
    scenario = Scenario(name, 'Loop over satellite link properties')
    teardowns = [
            teardown(scenario, '{} (Initial clean {} on {})'.format(name, mode, entity), entity, interfaces, mode)
            for entity, interfaces in (
                (args.pep_entity, args.pep_interfaces),
                (args.middlebox_entity, args.middlebox_interfaces))
            for mode in ('ingress', 'egress')
    ]


    legends.append('250M 3M Random loss')
    setups = [
            setup(scenario, '{} (Random loss ingress on pep)'.format(name), args.pep_entity, args.pep_interfaces, 'ingress', args.pep_bandwidth, args.pep_delay, 'random', [1.0], teardowns),
            setup(scenario, '{} (Random loss egress on pep)'.format(name), args.pep_entity, args.pep_interfaces, 'egress', args.pep_bandwidth, args.pep_delay, 'random', [1.0], teardowns),
            setup(scenario, '{} (Random loss bandwidth and delay ingress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'ingress', '250M', args.delay_server_to_client, wait_finished=teardowns),
            setup(scenario, '{} (Random loss bandwidth and delay egress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'egress', '3M', args.delay_client_to_server, wait_finished=teardowns),
    ]

    file_transfer = [add_download_scenario(scenario, '{} (Download on 250M 3M random link)'.format(name), args.server, args.client, args.duration, args.client_ip, args.port, args.file_size, args.post_processing_entity, setups)]

    teardowns = [
            teardown(scenario, '{} (Random loss clean {} on {})'.format(name, mode, entity), entity, interfaces, mode, file_transfer)
            for entity, interfaces in (
                (args.pep_entity, args.pep_interfaces),
                (args.middlebox_entity, args.middlebox_interfaces))
            for mode in ('ingress', 'egress')
    ]


    legends.append('250M 3M GE model')
    setups = [
            setup(scenario, '{} (GE model ingress on pep)'.format(name), args.pep_entity, args.pep_interfaces, 'ingress', args.pep_bandwidth, args.pep_delay, 'gemodel', [1.8, 64.5, 100.0, 0.0], teardowns),
            setup(scenario, '{} (GE model egress on pep)'.format(name), args.pep_entity, args.pep_interfaces, 'egress', args.pep_bandwidth, args.pep_delay, 'gemodel', [1.8, 64.5, 100.0, 0.0], teardowns),
            setup(scenario, '{} (GE model bandwidth and delay ingress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'ingress', '250M', args.delay_server_to_client, wait_finished=teardowns),
            setup(scenario, '{} (GE model bandwidth and delay egress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'egress', '3M', args.delay_client_to_server, wait_finished=teardowns),
    ]

    file_transfer = [add_download_scenario(scenario, '{} (Download on 250M 3M GE link)'.format(name), args.server, args.client, args.duration, args.client_ip, args.port, args.file_size, args.post_processing_entity, setups)]

    teardowns = [
            teardown(scenario, '{} (GE model clean {} on {})'.format(name, mode, entity), entity, interfaces, mode, file_transfer)
            for entity, interfaces in (
                (args.pep_entity, args.pep_interfaces),
                (args.middlebox_entity, args.middlebox_interfaces))
            for mode in ('ingress', 'egress')
    ]


    legends.append('250M 3M No loss')
    setups = [
            setup(scenario, '{} (250M 3M ingress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'ingress', '250M', args.delay_server_to_client, wait_finished=teardowns),
            setup(scenario, '{} (250M 3M egress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'egress', '3M', args.delay_client_to_server, wait_finished=teardowns),
    ]

    file_transfer = [add_download_scenario(scenario, '{} (Download on 250M 3M)'.format(name), args.server, args.client, args.duration, args.client_ip, args.port, args.file_size, args.post_processing_entity, setups)]

    teardowns = [
            teardown(scenario, '{} (250M 3M clean {} on middlebox)'.format(name, mode), args.middlebox_entity, args.middlebox_interfaces, mode, file_transfer)
            for mode in ('ingress', 'egress')
    ]


    legends.append('50M 10M No loss')
    setups = [
            setup(scenario, '{} (50M 10M ingress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'ingress', '50M', args.delay_server_to_client, wait_finished=teardowns),
            setup(scenario, '{} (50M 10M egress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'egress', '10M', args.delay_client_to_server, wait_finished=teardowns),
    ]

    file_transfer = [add_download_scenario(scenario, '{} (Download on 50M 10M)'.format(name), args.server, args.client, args.duration, args.client_ip, args.port, args.file_size, args.post_processing_entity, setups)]

    teardowns = [
            teardown(scenario, '{} (50M 10M clean {} on middlebox)'.format(name, mode), args.middlebox_entity, args.middlebox_interfaces, mode, file_transfer)
            for mode in ('ingress', 'egress')
    ]


    legends.append('10M 2M No loss')
    setups = [
            setup(scenario, '{} (10M 2M ingress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'ingress', '10M', args.delay_server_to_client, wait_finished=teardowns),
            setup(scenario, '{} (10M 2M egress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'egress', '2M', args.delay_client_to_server, wait_finished=teardowns),
    ]

    file_transfer = [add_download_scenario(scenario, '{} (Download on 10M 2M)'.format(name), args.server, args.client, args.duration, args.client_ip, args.port, args.file_size, args.post_processing_entity, setups)]

    teardowns = [
            teardown(scenario, '{} (10M 2M clean {} on middlebox)'.format(name, mode), args.middlebox_entity, args.middlebox_interfaces, mode, file_transfer)
            for mode in ('ingress', 'egress')
    ]


    legends.append('2M 10M No loss')
    setups = [
            setup(scenario, '{} (2M 10M ingress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'ingress', '2M', args.delay_server_to_client, wait_finished=teardowns),
            setup(scenario, '{} (2M 10M egress on middlebox)'.format(name), args.middlebox_entity, args.middlebox_interfaces, 'egress', '10M', args.delay_client_to_server, wait_finished=teardowns),
    ]

    file_transfer = [add_download_scenario(scenario, '{} (Download on 2M 10M)'.format(name), args.server, args.client, args.duration, args.client_ip, args.port, args.file_size, args.post_processing_entity, setups)]

    teardowns = [
            teardown(scenario, '{} (2M 10M clean {} on middlebox)'.format(name, mode), args.middlebox_entity, args.middlebox_interfaces, mode, file_transfer)
            for mode in ('ingress', 'egress')
    ]


    observer.launch_and_wait(scenario)

    results = DataProcessor(observer)
    iperf3_servers = scenario.extract_function_id(iperf3=iperf3_find_server, include_subscenarios=True)
    for legend, iperf3_server in zip(legends, iperf3_servers):
        results.add_callback(legend, extract_iperf_statistic, iperf3_server)
    plots = results.post_processing()
    
    figure, axis = plt.subplots()
    for legend, df in plots.items():
        df.columns = [legend]
        df.plot(ax=axis)

    plt.show()


if __name__ == '__main__':
    main()
