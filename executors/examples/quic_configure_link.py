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
 - The evolution of the received bit_rate
 - The evolution of the sent bit_rate
 - The evolution of the sent data
 - The evolution of the received data
 - The time needed to download the resources

+-----------+     +-----------------------+     +-----------+
| data      |<--->| delay/bandwidth       |<--->| data      |
| server    |     | limitation            |     | client    |
+-----------+     +-----------------------+     +-----------+
|  server_ip|     |                       |     |           |
|           |     | up_iface   down_iface |     |           |
+-----------+     +-----------------------+     +-----------+
| entity:   |     | entity:               |     | entity:   |
|  server   |     |  midbox (middle-box)  |     |  client   |
+-----------+     +-----------------------+     +-----------+

OpenBACH parameters:
 - post-processing-entity: entity where the post-processing will be performed
 - project_name: the name of the project
 - path: the path where the post processing data will be stored

Specific scenario parameters:
 - bandwidth_server_to_client: the bandwidth limitation in the
     server to client direction
 - bandwidth_client_to_server: the bandwidth limitation in the
     client to server direction
 - delay_server_to_client: the delay to add in the
     server to client direction
 - delay_client_to_server: the delay to add in the
     client to server direction
 - resources: resources to download in parallel over concurrent QUIC streams

Other parameters:
 - server_ip: ip address of the server
 - up_iface: Network interface name of the middlebox entity on which the delay and/or bandwidth
     limitation are applied in the client to server (uplink) direction 
 - down_iface: Network interface name of the middlebox entity on which the delay and/or bandwidth
     limitation are applied in the server to client (downlink) direction
 
Step-by-step description of the scenario:
 - teardown: clean the middle box interfaces
 - setup: set the middle box interfaces to emulate uplink and downlink paths
 - captures: capture network traffic to analyze
 - download: start the download of resources
 - analyzes: analyze captured traffic
 - teardown: clean the middle box interface
"""

import os
import sys
from scenario_builder import Scenario
from auditorium_scripts.scenario_observer import ScenarioObserver, DataProcessor
from scenario_builder.scenarios import network_configure_link, service_quic, transport_tcpdump
from scenario_builder.helpers.service.quic import quic_find_client

import pandas as pd
import matplotlib.pyplot as plt



DEFAULT_PCAPS_DIR = '/tmp/openbach_executors_examples/quic_configure_link'
TITLES = tuple()


def extract_quic_statistic(job):
    data = job.statistics.dated_data
    return [(timestamp, stats['download_time']) for timestamp, stats in data.items()]
    

def extract_tcpdump_statistic(job):
    data = job.statistics_data[('Flow1',)].dated_data
    timestamps = pd.Series(list(data), name=None)
    timestamps -= timestamps.min()
    return pd.DataFrame({'bit_rate': [stats['bit_rate'] for stats in data.values()],
                         'bytes_count': [stats['bytes_count'] for stats in data.values()]}, 
                         index=timestamps)


def setup(scenario, name, entity, interfaces, mode, bandwidth=None, delay_distribution='normal', delay=0, jitter=0, loss_model='random', loss_model_params=[0.0], buffer_size=50000, wait_finished=None):
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
    sub.configure(transport_tcpdump.build(entity, 'capture', capture_file, iface, src_ip, dst_ip, src_port, dst_port, proto, scenario_name=name))
    return sub


def transport_tcpdump_analyze_scenario(scenario, name, entity, capture_file, src_ip=None, dst_ip=None, src_port=None, dst_port=None, proto=None, metrics_interval=None, post_processing_entity=None, wait_finished=None):
    sub = scenario.add_function('start_scenario_instance', wait_finished=wait_finished)
    sub.configure(transport_tcpdump.build(entity, 'analyze', capture_file, None, src_ip, dst_ip, src_port, dst_port, proto, metrics_interval=metrics_interval, 
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
    interfaces = ','.join([args.up_iface, args.down_iface])
    teardowns = [
       teardown(
          scenario, 
          name='Clean {} on {} in {}'.format(interfaces, args.entity, mode), 
          entity=args.entity, 
          interfaces=interfaces, 
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
          interfaces=iface, 
          mode=mode, 
          bandwidth=bandwidth, 
          delay=delay,
          loss_model=args.loss_model,
          loss_model_params=args.loss_model_parameters, 
          wait_finished=teardowns
       )
       for name, iface, mode, bandwidth, delay in (('Set downlink path', args.down_iface, 'egress', args.bandwidth_server_to_client, args.delay_server_to_client),
                                                   ('Set uplink path', args.up_iface, 'egress', args.bandwidth_client_to_server, args.delay_client_to_server))
    ]
    if capture:
       # Add scenario to capture packets
       captures = [
          transport_tcpdump_capture_scenario(
             scenario, 
             name='Capture traffic {} by the {}'.format(direction, entity), 
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
          args.nb_runs,
          args.download_dir,
          args.server_log_dir,
          args.server_extra_args,
          args.client_log_dir,
          args.client_extra_args,
          args.post_processing_entity,
          wait_launched=captures if capture else None,
          wait_finished=setups
       )
    ]
    if capture:
       # Stop captures
       stop_captures = [stop_scenario(scenario, scenario_to_stop, wait_finished=downloads) for scenario_to_stop in captures] 

       # Add scenarios to analyze captured packets
       analyzes = [
          transport_tcpdump_analyze_scenario(
             scenario, 
             name='Analyze traffic {} by the {}'.format(direction, entity), 
             entity=entity, 
             capture_file=os.path.join(args.pcaps_dir, '{}_{}_{}.pcap'.format(args.server_implementation, args.client_implementation, direction)), 
             **fields, 
             proto='udp', 
             metrics_interval=50, 
             post_processing_entity=args.post_processing_entity, 
             wait_finished=captures
          ) 
          for entity, direction, fields in ((args.server, 'received', {'dst_ip':args.server_ip, 'dst_port':args.server_port}),
                                            (args.server, 'sent', {'src_ip':args.server_ip, 'src_port':args.server_port}),
                                            (args.client, 'received', {'src_ip':args.server_ip, 'src_port':args.server_port}),
                                            (args.client, 'sent', {'dst_ip':args.server_ip, 'dst_port':args.server_port}))
       ]
 
       global TITLES
       TITLES += ('{} received by the server', '{} sent by the server', '{} received by the client', '{} sent by the client')

    # Add scenarios to clear interfaces
    teardowns = [
       teardown(
          scenario, 
          name='Clean {} on {} in {}'.format(interfaces, args.entity, mode), 
          entity=args.entity, 
          interfaces=interfaces, 
          mode=mode,
          wait_finished=downloads
          
       )
       for mode in ('ingress', 'egress')
    ]
   



def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', '--middlebox-entity', '-e', required=True,
            help='Name of the middlebox entity')
    observer.add_scenario_argument(
            '--bandwidth-server-to-client', '-B', required=True,
            help='Bandwidth limitation in the server to client direction '
                 '(Kbps|Mbps|Gbps expressed as [value][K][M][G])')
    observer.add_scenario_argument(
            '--bandwidth-client-to-server', '-b', required=True,
            help='Bandwidth limitation in the client to server direction '
                 '(Kbps|Mbps|Gbps expressed as [value][K][M][G])')
    observer.add_scenario_argument(
            '--delay-server-to-client', '-D', required=True, type=int,
            help='Delay to add in the server to client direction (ms)')
    observer.add_scenario_argument(
            '--delay-client-to-server', '-d', required=True, type=int,
            help='Delay to add in the client to server direction (ms)')
    observer.add_scenario_argument(
            '--loss-model', '-lm', choices=['random', 'state', 'gemodel'],
            default='random', help='Packets loss model to use (only for apply operation)')
    observer.add_scenario_argument(
            '--loss-model-parameters', '-lmp', default=0.0, type=float, nargs='*',
            help='Packets loss model parameters to use (only for apply operation). Warning: '
            'This must not be the last argument of the scenario'
            'This could be used as follows:'
            '-lm random -lmp 1; to add 1% random losses'
            '-lm gemodel -lmp 1.8 64.5 100 0; to add P(g|g)= 0.982, P(g|b)= 0.645, P(b|b)= 0.355, P(b|g)= 0.018'
            '(see [RFC6534] for more details)')
    observer.add_scenario_argument(
            '--up-iface', '-msi', required=True,
            help='Network interface of the middlebox that is connected to the server')
    observer.add_scenario_argument(
            '--down-iface', '-mci', required=True,
            help='Network interface of the middlebox that is connected to the client')

    observer.add_scenario_argument(
            '--server', '-s', required=True,
            help='Name of the entity on which to run QUIC server')
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
            help='Name of the entity on which to run QUIC client')
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
            '--nb-runs', '-N', type=int, default=1,
            help='The number of times resources will be downloaded')
    observer.add_scenario_argument(
            '--pcaps-dir', '-W', default=DEFAULT_PCAPS_DIR,
            help='Path to the directory to save packets capture files on client and server')
    observer.add_scenario_argument(
            '--report-dir', '-R', default='/tmp',
            help='Path to the directory to save generated figures')

    observer.add_scenario_argument(
            '--post-processing-entity', 
            help='The entity where the post-processing will be performed '
                 '(histogram/time-series jobs must be installed) if defined')
    args = observer.parse(argv)

    name = args.scenario_name
    
    download_times, timestamps = list(), list()
    for run_number in range(args.nb_runs):
        # Built main scenario
        scenario = Scenario(name, 'Download resources using QUIC under a given network condition.'
                                  ' Exchanged packets are captured and then analyzed')
        build(scenario, args, capture=run_number==0)
        observer.launch_and_wait(scenario)
        results = DataProcessor(observer)
        quic_client, = scenario.extract_function_id(quic=quic_find_client, include_subscenarios=True)
        results.add_callback('download_time', extract_quic_statistic, quic_client)
        if run_number == 0:
           tcpdump_analyzes = scenario.extract_function_id("pcap_postprocessing", include_subscenarios=True)
           for title, tcpdump_analyze in zip(TITLES, tcpdump_analyzes):
               results.add_callback(title, extract_tcpdump_statistic, tcpdump_analyze)

           plots = results.post_processing()

           for title, df in plots.items():
               if title in TITLES:
                  for stat_name, ts_xlabel, ts_ylabel, ts_title in (
                      ('bit_rate', 'Time (ms)', 'Bit Rate (Kbps)', title.format('Bit Rate')), 
                      ('bytes_count', 'Time (ms)', 'Bytes Count (B)', title.format('Bytes Count'))): 
                      figure, axis = plt.subplots()
                      plt.xlabel(ts_xlabel)
                      plt.ylabel(ts_ylabel)
                      df.plot(y=stat_name, ax=axis, title=ts_title, grid=True, legend=False)
                      figure_name = '{}_{}_{}.png'.format(args.server_implementation, args.client_implementation, ts_title.replace(' ','-'))
                      figure_path = os.path.join(args.report_dir, figure_name)
                      plt.savefig(figure_path)

        else: 
           plots = results.post_processing()
        try:
           data = plots['download_time']
           timestamps.append(data[0][0])
           download_times.append(data[0][1])
        except KeyError as ex:
               message = ("No 'download_time' available meaning that no statistic when postprocessing quic scenario. "
                          "May be the scenario failed")
               print(message)
               sys.exit(message)
        
    timestamps = [timestamp - min(timestamps) for timestamp in timestamps]
    df = pd.DataFrame({'download_time': download_times}, index=timestamps)
    for stat_name, ts_xlabel, ts_ylabel, ts_title, cdf_xlabel, cdf_ylabel, cdf_title in (
        ('download_time', 'Time (ms)', 'Download Time (ms)', 'Download Time TS', 'Download Time (ms)', 'CDF', 'Download Time CDF'),):
        figure, axis = plt.subplots()
        plt.xlabel(ts_xlabel)
        plt.ylabel(ts_ylabel)
        df.plot(y=stat_name, ax=axis, title=ts_title, grid=True, legend=False, linewidth=2)
        figure_name = '{}_{}_{}_ts.png'.format(args.server_implementation, args.client_implementation, 'download_time')
        figure_path = os.path.join(args.report_dir, figure_name)
        plt.savefig(figure_path)
        if args.nb_runs > 1:
           figure, axis = plt.subplots()
           plt.xlabel(cdf_xlabel)
           plt.ylabel(cdf_ylabel)
           df.plot(kind='hist', y=stat_name, ax=axis, title=cdf_title, grid=True, legend=False, histtype='step', bins=100, cumulative=1, normed=True)
           figure_name = '{}_{}_{}_cdf.png'.format(args.server_implementation, args.client_implementation, 'download_time')
           figure_path = os.path.join(args.report_dir, figure_name)
           plt.savefig(figure_path)
           



if __name__ == '__main__':
    main()
