#!/usr/bin/env python

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2020 CNES
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
 - The evolution of the received bit_rate
 - The evolution of the sent bit_rate
 - The evolution of the sent data
 - The time needed to receive the file

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
import os
from scenario_builder import Scenario
from auditorium_scripts.scenario_observer import ScenarioObserver, DataProcessor
from scenario_builder.scenarios import network_configure_link, service_quic, transport_tcpdump
from scenario_builder.helpers.service.quic import quic_find_client
from scenario_builder.helpers.transport.tcpdump import tcpdump_find_analyze

import pandas as pd
import matplotlib.pyplot as plt



DEFAULT_PCAPS_DIR = '/tmp/openbach_executors_examples/quic_configure_link'
legends = tuple()


def extract_quic_statistic(job):
    data = job.statistics.dated_data
    return [
            (timestamp, stats['download_time'])
            for timestamp, stats in data.items()
    ]


def extract_tcpdump_statistic(job):
    data = job.statistics_data[('Flow1',)].dated_data
    timestamps = pd.Series(data.keys(), name=None)
    timestamps -= timestamps.min
    return pd.DataFrame({'bit_rate': [stats['bit_rate'] for stats in data.values()],
                         'bytes_count': [stats['bytes_count'] for stats in data.values()]}, 
                         index=timestamps)


def setup(scenario, name, entity, interfaces, mode, bandwidth=None, delay_distribution='normal', delay=0, jitter=0, loss_model='random', loss_model_params=[0.0], buffer_size=10000, wait_finished=None):
    sub = scenario.add_function('start_scenario_instance', wait_finished=wait_finished)
    sub.configure(network_configure_link.build(entity, interfaces, mode, 'apply', bandwidth, delay, jitter, delay_distribution, loss_model, loss_model_params, buffer_size, name))
    return sub


def service_quic_scenario(scenario, server, server_ip, server_port, server_implementation, client, client_implementation, resources, nb_runs, download_dir, server_log_dir, server_extra_args, client_log_dir, client_extra_args, post_processing_entity, wait_launched=None, wait_finished=None):
    sub = scenario.add_function('start_scenario_instance', wait_launched=wait_launched, wait_finished=wait_finished)
    sub.configure(service_quic.build(server, server_ip, server_port, server_implementation, client, client_implementation, resources, nb_runs, 
                                     download_dir, server_log_dir, server_extra_args, client_log_dir, client_extra_args, post_processing_entity))
    return sub


def transport_tcpdump_capture_scenario(scenario, name, entity, iface, capture_file, src_ip=None, dst_ip=None, src_port=None, dst_port=None, proto=None, wait_finished=None):
    sub = scenario.add_function('start_scenario_instance', wait_finished=wait_finished)
    sub.configure(transport_tcpdump.build(entity, 'capture', iface, capture_file, src_ip, dst_ip, src_port, dst_port, proto, scenario_name=name))
    return sub


def transport_tcpdump_analyze_scenario(scenario, name, entity, capture_file, src_ip=None, dst_ip=None, src_port=None, dst_port=None, proto=None, metrics_interval=None, post_processing_entity=None, wait_finished=None):
    sub = scenario.add_function('start_scenario_instance', wait_finished=wait_finished)
    sub.configure(transport_tcpdump.build(entity, 'analyze', None, capture_file, src_ip, dst_ip, src_port, dst_port, proto, metrics_interval=metrics_interval, 
                                          post_processing_entity=post_processing_entity, scenario_name=name))
    return sub


def stop_scenario(scenario, scenario_to_stop, wait_finished=None):
    sub = scenario.add_function('stop_scenario_instance', wait_finished=wait_finished)
    sub.configure(scenario_to_stop)
    return sub 


def teardown(scenario, name, entity, interfaces, mode, wait_finished=None):
    sub = scenario.add_function('start_scenario_instance', wait_finished=wait_finished)
    sub.configure(network_configure_link.build(entity, interfaces, mode, 'clear', scenario_name=name))
    return sub


def build(scenario, args, capture=False):
    # Add scenarios to clear interfaces
    teardowns = [
       teardown(
          scenario, 
          name='Clean {} on {} in {}'.format(args.middlebox_interfaces, args.entity, mode), 
          entity=args.entity, 
          interfaces=args.middlebox_interfaces, 
          mode=mode
       )
       for mode in ('ingress', 'egress')
    ]

    # Add scenarios to set interfaces
    setups = [
       setup(
          scenario, 
          name=name, 
          entity=args.entity, 
          interfaces=args.middlebox_interfaces, 
          mode=mode, 
          bandwidth=bandwidth, 
          delay=delay, 
          wait_finished=teardowns
       )
       for name, mode, bandwidth, delay in (('Set downlink path', 'ingress', args.bandwidth_server_to_client, args.delay_server_to_client),
                                            ('Set uplink path', 'egress', args.bandwidth_client_to_server, args.delay_client_to_server))
    ]
    if capture:
       # Add scenario to capture packets
       captures = [
          transport_tcpdump_capture_scenario(
             scenario, 
             name='Capture traffic {} by {}'.format(direction, entity), 
             entity=entity, 
             iface='any', 
             capture_file=os.path.join(args.pcaps_dir, '{}_{}_{}.pcap'.format(args.server_implementation, args.client_implementation, direction)), 
             **fields, 
             proto='udp', 
             wait_finished=setups
          ) 
          for entity, direction, fields in ((args.server, 'received', {'dst_ip':args.server_ip, 'dst_port':args.server_port}),
                                            (args.server, 'sent', {'src_ip':args.server_ip, 'src_port':args.server_port}),
                                            (args.client, 'received', {'src_ip':args.server_ip, 'src_port':args.server_port}),
                                            (args.client, 'sent', {'dst_ip':args.server_ip, 'dst_port':args.server_port}))
       ]
    
    # Add scenario to download resources
    downloads = [
       service_quic_scenario(
          scenario,
          args.server,
          args.server_ip,
          args.server_port,
          args.server_implementation,
          args.client,
          args.client_implementation,
          args.resources,
          1,
          args.download_dir,
          args.server_log_dir,
          args.server_extra_args,
          args.client_log_dir,
          args.client_extra_args,
          args.post_processing_entity,
          wait_launched=captures if capture else None
       )
    ]
    if capture:
       # Stop captures
       stop_captures = [stop_scenario(scenario, scenario_to_stop, wait_finished=downloads) for scenario_to_stop in captures] 

       # Add scenarios to analyze captured packets
       analyzes = [
          transport_tcpdump_analyze_scenario(
             scenario, 
             name='Analyze traffic {} by {}'.format(direction, entity), 
             entity=entity, 
             capture_file=os.path.join(args.pcaps_dir, '{}_{}_{}.pcap'.format(args.server_implementation, args.client_implementation, direction)), 
             **fields, 
             proto='udp', 
             metrics_interval=100, 
             post_processing_entity=args.post_processing_entity, 
             wait_finished=captures
          ) 
          for entity, direction, fields in ((args.server, 'received', {'dst_ip':args.server_ip, 'dst_port':args.server_port}),
                                            (args.server, 'sent', {'src_ip':args.server_ip, 'src_port':args.server_port}),
                                            (args.client, 'received', {'src_ip':args.server_ip, 'src_port':args.server_port}),
                                            (args.client, 'sent', {'dst_ip':args.server_ip, 'dst_port':args.server_port}))
       ]
    
       global legends 
       legends = legends + ('traffic_received_server', 'traffic_sent_server', 'traffic_received_client', 'traffic_sent_client')
    # Add scenarios to clear interfaces
    teardowns = [
       teardown(
          scenario, 
          name='Clean {} on {} in {})'.format(args.middlebox_interfaces, args.entity, mode), 
          entity=args.entity, 
          interfaces=args.middlebox_interfaces, 
          mode=mode,
          wait_finished=downloads
          
       )
       for mode in ('ingress', 'egress')
    ]
   



def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', '--configure-link-entity', '-e', required=True,
            help='Name of the entity where configure link should run')
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
            '--middlebox-interfaces', '--interfaces', '-m', required=True,
            help='Comma-separated list of the network interfaces to emulate link on on the middlebox')

    observer.add_scenario_argument(
            '--server', '-s', required=True,
            help='name of the entity on which to run QUIC server')
    observer.add_scenario_argument(
            '--server-ip', '-A', required=True,
            help='The IP address of the QUIC server')
    observer.add_scenario_argument(
            '--server-port', '-P', default=4433,
            help='The port of the server to connect to/listen on')
    observer.add_scenario_argument(
            '--server-implementation', '-I', required=True,
            help='The QUIC implementation to run by the server. Possible values are: ngtcp2, picoquic, quicly')
    observer.add_scenario_argument(
            '--client', '-c', required=True,
            help='name of the entity on which to run QUIC client')
    observer.add_scenario_argument(
            '--client-implementation', '-i', required=True,
            help='The QUIC implementation to run by the client. Possible values are: ngtcp2, picoquic, quicly')
    observer.add_scenario_argument(
            '--resources', '-r', required=True,
            help='Comma-separed list of resources to download in parallel over concurrent streams')
    observer.add_scenario_argument(
            '--download-dir', '-w',
            help='The path to the directory to save downloaded resources')
    observer.add_scenario_argument(
            '--server-log-dir', '-L',
            help='The path to the directory to save server\'s logs')
    observer.add_scenario_argument(
            '--server-extra-args', '-X',
            help='Specify additional CLI arguments that are supported by the chosen server implementation')
    observer.add_scenario_argument(
            '--client-log-dir', '-l',
            help='The path to the directory to save client\'s logs')
    observer.add_scenario_argument(
            '--client-extra-args', '-x',
            help='Specify additional CLI arguments that are supported by the chosen client implementation')
    observer.add_scenario_argument(
            '--nb-runs', '-N', default=1,
            help='The number of times resources will be downloaded')
    observer.add_scenario_argument(
            '--pcaps-dir', '-W', default=DEFAULT_PCAPS_DIR,
            help='Path to directory to save packets capture files on client and server')
    observer.add_scenario_argument(
            '--report-dir', '-R', default='/tmp',
            help='Path to directory to save generated figures')

    observer.add_scenario_argument(
            '--post-processing-entity', 
            help='The entity where the post-processing will be performed '
                 '(histogram/time-series jobs must be installed) if defined')
    args = observer.parse(argv)

    name = args.scenario_name
    scenario = Scenario(name, 'Download resources using QUIC and capture exchanged packets for debugging/analyzing')
    
    download_times = list()
    for run_number in range(args.nb_runs):
        # Built main scenario
        build(scenario, args, capture=run_number==0)
        observer.launch_and_wait(scenario)
        results = DataProcessor(observer)
        quic_client, = scenario.extract_function_id(quic=quic_find_client, include_subscenarios=True)
        results.add_callback('download_time', extract_quic_statistic, quic_client)
        if run_number == 0:
           tcpdump_analyzes = scenario.extract_function_id(tcpdump=tcpdump_find_analyze, include_subscenarios=True)
           for legend, tcpdump_analyze in zip(legends, tcpdump_analyzes):
               print('{}:{}'.format(legend, tcpdump_analyze))
               results.add_callback(legend, extract_tcpdump_statistic, tcpdump_analyze)

           plots = results.post_processing()
           print(plots)
           for legend, df in plots.items():
               print(df)
               figure, axis = plt.subplots()
               df.columns = [legend]
               df.plot(ax=axis)
               filename = '{}_{}_{}.png'.format(args.server_implementation, args.client_implementation, legend)
               filepath = os.path.join(args.report_dir, filename)
               plt.show()
               plt.savefig(filepath)

        else: 
           plots = results.post_processing()
        #download_times.append(plots['download_time'])
    #print(download_times)
    #timestamps -= timestamps.min
    #pd.DataFrame({'download_time': [stats['download_time'] for stats in data.values()]}, index=timestamps)



if __name__ == '__main__':
    main()
