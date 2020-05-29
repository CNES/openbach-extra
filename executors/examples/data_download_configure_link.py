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

Data is transmitted from a server to a client
The test reports
 - The evolution of the received goodput
 - The time needed to receive 10%, 50% and 100% of the file

+-----------+     +-----------------------+     +-----------+
| data      |<--->| delay/bandwidth       |<--->| data      |
| server    |     | limitation            |     | client    |
+-----------+     +-----------------------+     +-----------+
|  server_ip|     |                       |     |client_ip  |
|           |     |              midbox_if|     |           |
+-----------+     +-----------------------+     +-----------+
| entity:   |     | entity:               |     | entity:   |
|  server   |     |  midbox (middle-box)  |     |  client   |
+-----------+     +-----------------------+     +-----------+

OpenBACH parameters:
 - entity_pp : entity where the post-processing will be performed
 - project_name : the name of the project
 - path : the path where the post processing data will be stored

Specific scenario parameters:
 - file_size : the size of the file to transmit
 - bandwidth_server_to_client : the bandwidth limitation in the
     server to client direction
 - bandwidth_client_to_server : the bandwidth limitation in the
     client to server direction
 - delay_server_to_client : the delay limitation in the
     server to client direction
 - delay_client_to_server : the delay limitation in the
     client to server direction

Other parameters:
 - server_ip : ip address of the server
 - client_ip : ip address of the client
 - midbox_if: Interface name on which the delay and/or bandwidth
     limitation is introduced

Step-by-step description of the scenario:
 - clean-midbox-if : clean the middle box interface
 - add-limit-if : add delay and/or bandwidth limitations in both
     directions on midbox-if                                      
 - qos-eval : run QoS evaluation in both direction
 - download : start the download of file_size
 - clean-midbox-if : clean the middle box interface
"""


from auditorium_scripts.scenario_observer import ScenarioObserver, DataProcessor
from scenario_builder.scenarios import network_configure_link, service_data_transfer
from scenario_builder.helpers.transport.iperf3 import iperf3_find_server


def extract_iperf_statistic(job):
    data = job.statistics_data[('Flow1',)].dated_data
    return [
            (timestamp, stats['throughput'])
            for timestamp, stats in data.items()
    ]


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', '--configure-link-entity', '-e', required=True,
            help='Name of the entity where configure link should run')
    observer.add_scenario_argument(
            '--server', '--data-transfer-server', '-s', required=True,
            help='Name of the entity where the data transfer server should run')
    observer.add_scenario_argument(
            '--client', '--data-transfer-client', '-c', required=True,
            help='Name of the entity where the data transfer client should run')
    observer.add_scenario_argument(
            '--post-processing-entity',
            help='Name of the entity where the post-processing jobs should run')
    observer.add_scenario_argument(
            '--file-size', '--size', '-f', required=True,
            help='Size of the file transfer')
    observer.add_scenario_argument(
            '--duration', '-l', default=10, type=int,
            help='Duration of the file transfer')
    observer.add_scenario_argument(
            '--bandwidth-server-to-client', '-B', required=True,
            help='Bandwidth allocated for the server to answer the client')
    observer.add_scenario_argument(
            '--bandwidth-client-to-server', '-b', required=True,
            help='Bandwidth allocated for the client to ask the server')
    observer.add_scenario_argument(
            '--delay-server-to-client', '-D', required=True, type=int,
            help='Delay for a packet to go from the server to the client')
    observer.add_scenario_argument(
            '--delay-client-to-server', '-d', required=True, type=int,
            help='Delay for a packet to go from the client to the server')
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
            '--middlebox-interfaces', '--interfaces', '-m', required=True,
            help='Comma-separated list of the network interfaces to emulate link on on the middlebox')

    args = observer.parse(argv)

    print('Clearing interfaces')
    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            'clear',
            args.bandwidth_server_to_client,
            args.delay_server_to_client)
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            'clear',
            args.bandwidth_client_to_server,
            args.delay_client_to_server)
    observer.launch_and_wait(scenario)

    print('Setting interfaces')
    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            'apply',
            args.bandwidth_server_to_client,
            args.delay_server_to_client)
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            'apply',
            args.bandwidth_client_to_server,
            args.delay_client_to_server)
    observer.launch_and_wait(scenario)

    print('Download', args.file_size, 'MB')
    scenario = service_data_transfer.build(
            args.server,
            args.client,
            args.duration,
            args.client_ip,
            args.port,
            args.file_size,
            0x04,
            1400,
            args.post_processing_entity)
    observer.launch_and_wait(scenario)

    results = DataProcessor(observer)
    iperf3_server, = scenario.extract_function_id(iperf3=iperf3_find_server, include_subscenarios=True)
    results.add_callback('transfer', extract_iperf_statistic, iperf3_server)
    data = results.post_processing()
    print('Results from data transfer:', data['transfer'])

    print('Clearing interfaces')
    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            'clear',
            args.bandwidth_server_to_client,
            args.delay_server_to_client)
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            'clear',
            args.bandwidth_client_to_server,
            args.delay_client_to_server)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
