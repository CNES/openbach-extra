#!/usr/bin/env python

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2023 CNES
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

+-----------+     +-------------------------+     +-----------+
| data      |     | delay/loss/bandwidth    |<--->| data      |
| server    |     | limitation              |     | client    |
+-----------+     +-------------------------+     +-----------+
|           |     |                         |     |client_ip  |
|           |<--->|             midbox_iface|<--->|           |
+-----------+     +-------------------------+     +-----------+
| entity:   |     | entity:                 |     | entity:   |
|  server   |     |  midbox (middle-box)    |     |  client   |
+-----------+     +-------------------------+     +-----------+

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
 - loss_model_server_to_client : the loss model in the
     server to client direction
 - loss_model_client_to_server : the loss model in the
     client to server direction
 - loss_value_server_to_client : the loss value in the
     server to client direction
 - loss_value_client_to_server : the loss value in the
     client to server direction

Path characteristics of reference communication systems:
 # WLAN (proposed by default):
   - Bandwidth : 20-30 Mbps
   - Delay : 20-35 ms
   - Loss model : random
   - Loss value (pourcentage of losses): 1-2 %
 # 3G :
   - Bandwidth : 3-5 Mbps
   - Delay : 65-75 ms
   - Loss model : random
   - Loss value (pourcentage of losses): 0 %
 # Satellite End-to-End (including congestion losses):
   - Bandwidth : 10 Mbps
   - Delay : 250 ms
   - Loss model : gemodel
   - Loss value (Gilert-Elliot transition probabilities): p r 1-h 1-k
        - p: 0.017 (probability to move from good to bad state)
        - r: 0.935 (probability to move from bad to good state)
        - 1-h: 100 (loss probability in bad state)
        - 1-k: 0 (loss probability in good state) 
    (http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.303.7914&rep=rep1&type=pdf)
    (see tc_configure_link job help files for more information)

--> Path characteristics in accordance with the following sources :
    - Is Multi-Path Transport Suitable for Latency Sensitive Traffic?
      COMNET. 105. 10.1016/j.comnet.2016.05.008.
    - QUIC: Opportunities and threats in SATCOM
      https://www.tesa.prd.fr/documents/26/quic_1570652837.pdf

Other parameters:
 - client_ip : ip address of the client
 - midbox_if: Interface name on which the delay and/or bandwidth limitation 
     and/or packet losses is introduced (interface connected to the client)

Step-by-step description of the scenario:
 - clean-midbox-if : clean the middle box interface
 - add-limit-if : add delay and/or bandwidth limitations and/or packet losses
      in both directions on midbox-if                                      
 - qos-eval : run QoS evaluation in both direction
 - download : start the download of file_size
 - clean-midbox-if : clean the middle box interface
"""


from auditorium_scripts.scenario_observer import ScenarioObserver, DataProcessor
from scenario_builder.scenarios import network_configure_link, service_data_transfer
from scenario_builder.helpers.transport.iperf3 import iperf3_find_server


def extract_iperf_statistic(job):
    """Extract the `throughput` stat from the statistics generated by
    an iperf3 job.

    It is assumed that the server is connected to a single client
    (which is the case using the `service_data_transfer` scenario)
    hence the use of the `Flow1` suffix for the desired statistic.
    """
    data = job.statistics_data[('Flow1',)].dated_data
    return [
            (timestamp, stats['throughput'])
            for timestamp, stats in data.items() if stats.__contains__('throughput')
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
            help='Size of the file transfer (bytes expressed as [value][M|K|G])')
    observer.add_scenario_argument(
            '--duration', '-l', default=10, type=int,
            help='Duration of the file transfer (seconds)')
    observer.add_scenario_argument(
            '--bandwidth-server-to-client', '-B', default='25M',
            help='Bandwidth allocated for the server to answer the '
            'client (Mbps|Kbps expressed as [value][M|K])')
    observer.add_scenario_argument(
            '--bandwidth-client-to-server', '-b', default='25M',
            help='Bandwidth allocated for the client to ask the '
            'server (Mbps|Kbps expressed as [value][M|K])')
    observer.add_scenario_argument(
            '--delay-server-to-client', '-D', default=10, type=int,
            help='Delay for a packet to go from the server to the client (ms)')
    observer.add_scenario_argument(
            '--delay-client-to-server', '-d', default=10, type=int,
            help='Delay for a packet to go from the client to the server (ms)')
    observer.add_scenario_argument(
            '--loss-model-server-to-client', choices=['random', 'state', 'gemodel'], default='random',
            help='Packet loss model applied in the server to the client direction')
    observer.add_scenario_argument(
            '--loss-model-client-to-server', choices=['random', 'state', 'gemodel'], default='random',
            help='Packet loss model applied in the client to the server direction')
    observer.add_scenario_argument(
            '--loss-value-server-to-client', type=float, nargs='+', default=[1.0],
            help='Loss value applied in the server to the client direction'
            '(percentage or Gilbert-Elliot transition probabilities; '
            'see tc_configure_link job help files for more information)')
    observer.add_scenario_argument(
            '--loss-value-client-to-server', type=float, nargs='+', default=[1.0],
            help='Loss value applied in the client to the server direction'
            '(percentage or Gilbert-Elliot transition probabilities; '
            'see tc_configure_link job help files for more information)')
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

    # Setup link constraints using prebuilt scenarios
    print('Clearing interfaces')
    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            'clear')
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            'clear')
    observer.launch_and_wait(scenario)

    print('Setting interfaces')
    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            'apply',
            args.bandwidth_client_to_server,
            args.delay_client_to_server,
            loss_model=args.loss_model_client_to_server,
            loss_model_params=args.loss_value_client_to_server)
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            'apply',
            args.bandwidth_server_to_client,
            args.delay_server_to_client,
            loss_model=args.loss_model_server_to_client,
            loss_model_params=args.loss_value_server_to_client)
    observer.launch_and_wait(scenario)

    # Test a file transfer using prebuilt scenario
    print('Download', args.file_size, 'Bytes')
    scenario = service_data_transfer.build(
            args.client,
            args.server,
            args.client_ip,
            args.port,
            args.duration,
            args.file_size,
            0x04,
            1400,
            args.post_processing_entity)
    observer.launch_and_wait(scenario)

    # Post process the result of the last scenario
    results = DataProcessor(observer)
    # Here we are only interested into the data from the iperf3 server job
    # Since we know the `service_data_transfer` only launch one such job, we can
    # easily get its ID path (including subscenario instance IDs)
    iperf3_server, = scenario.extract_function_id(iperf3=iperf3_find_server, include_subscenarios=True)
    # Tell the post processor how we want to extract the data from our job and
    # under which key we want to get those data back. We do it once here but we
    # can register as many callback as necessary, they will run on the same data
    # once it has been fetched.
    results.add_callback('transfer', extract_iperf_statistic, iperf3_server)
    # Actually fetches raw data and run them through each registered callbacks
    data = results.post_processing()
    # From here on, we can do anything with our massaged data. This example
    # offers a simple `print`, but `matplotlib.pyplot` is most likely what
    # you’ll be after
    print('Results from data transfer:', data['transfer'])

    # Cleanup after ourselves using prebuilt scenario
    print('Clearing interfaces')
    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            'clear')
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            'clear')
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
