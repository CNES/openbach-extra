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

"""TCP Evaluation Suite

This scenario provides a scenario that enables the evaluation of TCP
congestion controls.

The architecture should be the following

   +--------------+                                +--------------+
   | endpointA    |                                | endpointC    |
   +--------------+----+                  +--------+--------------+
                       |                  |
                     +-+-------+     +---------+
                     |Router L |     |Router R |
                     +-+-------+-----+-------+-+
                       |                     |
   +--------------+----+                     +-----+--------------+
   | endpointB    |                                | endpointD    |
   +--------------+                                +--------------+

Here are the values that should be specified by default but available for
parametrisation by the user.

For a better understanding regarding the parameters example, the following
architecture include ips and interface name examples.

+---------+ensA: 192.168.0.5                       ensC: 192.168.3.4+---------+
|endpointA|(N 192.168.0.0/24)                     (N 192.168.3.0/24)|endpointC|
+---------+-------+                                        +--------+---------+
                  |                                        |
                  |                                        |
                  |ensL1: 192.168.0.14                     |ensR1: 192.168.3.3 
                  |(N 192.168.0.0/24)                      |(N 192.168.3.0/24)
                +-+-----+        ensR3: 192.168.2.25 +-----+-+
                |RouterL|          (N 192.168.2.0/24)|RouterR|
                +-+-----+----------------------------+-----+-+
ensL2: 192.168.1.5|   ensL3: 192.168.2.15                  |ensR2: 192.168.4.8 
(N 192.168.1.0/24)|   (N 192.168.2.0/24)                   |(N 192.168.4.0/24)
                  |                                        |
                  |                                        | 
+---------+-------+                                        +--------+---------+
|endpointB|ensB: 192.168.1.6                      ensD: 192.168.4.14|endpointD|
+---------+(N 192.168.1.0/24)                     (N 192.168.4.0/24)+---------+

+-------------------------------------+
endpointA and endpointC parameters:
  - Congestion control : CUBIC
  - IW : 10
endpointB and endpointD parameters:
  - Congestion control : CUBIC
  - IW : 10
endpointA <-> Router L,
endpointB <-> Router L,
Router R <-> endpointC,
Router R <-> endpointD,
  - bandwidth : 100 Mbps
  - latency : 10 ms
  - loss : 0%
Router L <-> Router R:
  - bandwidth : 20 Mbps
  - latency : 10 ms
  - loss : 0%
    at t=0+10s
  - bandwidth : 10 Mbps
  - latency : 10 ms
  - loss : 0%
    at t=10+10s
  - bandwidth : 20 Mbps
  - latency : 10 ms
  - loss : 0%
+-------------------------------------+


+-------------------------------------+
Pep redirect all interfaces for R and L:
  - pep on link LR
  - pep on link RL
+-------------------------------------+

+-------------------------------------+
Traffic:
  - direction_A-C : forward or return
    (default forward)
  - direction_B-D : forward or return
    (default forward)
  - flow_size_B-D :
    - start at tBD=0
    - 500 MB
    - n_flow = 1 (can be 0)
  - flow_size_A-C :
    - start at tAC=tBD+5 sec
    - 10 MB
    - n_flow : 1
    - repeat : 10
+-------------------------------------+

+-------------------------------------+
Metrics:
  - CWND for all the flows as function of time
  - Received throughput at the receiver for all entities receiving data as a function of time
  - Time needed to transmit flow_A-C (CDF)
  - bandwidth L <-> R usage (%) as function of time
+-------------------------------------+
"""


from auditorium_scripts.scenario_observer import ScenarioObserver, DataProcessor
from scenario_builder.scenarios import tcp_evaluation_suite
from scenario_builder.helpers.transport.iperf3 import iperf3_find_client

from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
import tempfile
import tarfile
import shutil


def extract_iperf_statistic(job):
    """Extract the `download_time` stat from the statistics generated by
    an iperf3 job.

    It is assumed that the server is connected to a single client
    (which is the case using the `service_data_transfer` scenario)
    hence the use of the `Flow1` suffix for the desired statistic.
    """
    data = job.statistics_data[('Flow1',)].dated_data
    return [
            (timestamp, stats['download_time'])
            for timestamp, stats in data.items() if 'download_time' in stats
    ]


def register_figure(path, scenario_id, observer_file, figure_type):
    if path is None:
        plt.show()
    else:
        figure_name = '{}_{}_{}.png'.format(scenario_id, 'download_time', figure_type)
        if not observer_file:
            plt.savefig(path.joinpath(figure_name).as_posix())
        else:
            archive =  path / f'scenario_instance_{scenario_id}.tar.gz'
            in_memory_figure = BytesIO()
            plt.savefig(in_memory_figure, format='png')
            infos_figure = tarfile.TarInfo(figure_name)
            infos_figure.size = in_memory_figure.tell()
            in_memory_figure.seek(0)

            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp_tar:
                with tarfile.open(archive.as_posix(), 'r:gz') as reading_tar, tarfile.open(fileobj=tmp_tar, mode='w:gz') as output_tar:
                    for member in reading_tar:
                        output_tar.addfile(member, reading_tar.extractfile(member.name))
                    output_tar.addfile(infos_figure, in_memory_figure)
            shutil.move(tmp_tar.name, archive)


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--endpointA', required=True,
            help='Name of the entity hosting endpointA (e.g. "endpointA")')
    observer.add_scenario_argument(
            '--endpointB', required=True,
            help='Name of the entity hosting endpointB (e.g. "endpointB")') 
    observer.add_scenario_argument(
            '--endpointC', required=True,
            help='Name of the entity hosting endpointC (e.g. "endpointC")') 
    observer.add_scenario_argument(
            '--endpointD', required=True,
            help='Name of the entity hosting endpointD (e.g. ""endpointD")')
    observer.add_scenario_argument(
            '--endpointC-ip', required=True,
            help='IP of endpointC on the network shared with routerR (e.g. "192.168.3.4")')
    observer.add_scenario_argument(
            '--endpointD-ip', required=True,
            help='IP of endpointD on the network shared with routerR (e.g. "192.168.4.14")')
    observer.add_scenario_argument(
            '--routerL', required=True,
            help='Name of the entity hosting routerL (e.g. "routerL")')
    observer.add_scenario_argument(
            '--routerR', required=True,
            help='Name of the entity hosting routerR (e.g. "routerR")')
    observer.add_scenario_argument(
            '--endpointA-network-ip', required=True,
            help='Network mask of the IP network shared by endpointA and routerL (e.g. "192.168.0.0/24")')
    observer.add_scenario_argument(
            '--endpointB-network-ip', required=True,
            help='Network mask of the IP network shared by endpointB and routerL (e.g. "192.168.1.0/24")')
    observer.add_scenario_argument(
            '--endpointC-network-ip', required=True,
            help='Network mask of the IP network shared by endpointC and routerR(e.g. "192.168.3.0/24")')
    observer.add_scenario_argument(
            '--endpointD-network-ip', required=True,
            help='Network mask of the IP network shared by endpointD and routerR (e.g. "192.168.4.0/24")')
    observer.add_scenario_argument(
            '--routerL-to-endpointA-ip', required=True,
            help='IP address of routerL on the network shared with endpointA (e.g. "192.168.0.14")')
    observer.add_scenario_argument(
            '--routerL-to-endpointB-ip', required=True,
            help='IP address of routerL on the network shared with endpointB (e.g. "192.168.1.5")')
    observer.add_scenario_argument(
            '--routerR-to-endpointC-ip', required=True,
            help='IP address of routerR on the network shared with endpointC (e.g. "192.168.3.3")')
    observer.add_scenario_argument(
            '--routerR-to-endpointD-ip', required=True,
            help='IP address of routerR on the network shared with endpointD (e.g. "192.168.4.8")')
    observer.add_scenario_argument(
            '--routerL-to-routerR-ip', required=True,
            help='IP address of routerL on the network shared with routerR (e.g. "192.168.2.15")')
    observer.add_scenario_argument(
            '--routerR-to-routerL-ip', required=True,
            help='IP address of routerR on the network shared with routerL (e.g. "192.168.2.25")')
    observer.add_scenario_argument(
            '--interface-AL', required=True,
            help='Name of the interface on endpointA towards routerL (e.g. "ensA")')
    observer.add_scenario_argument(
            '--interface-BL', required=True,
            help='Name of the interface on endpointB towards routerL (e.g. "ensB")')
    observer.add_scenario_argument(
            '--interface-CR', required=True,
            help='Name of the interface on endpointC towards routerR (e.g. "ensC")')
    observer.add_scenario_argument(
            '--interface-DR', required=True,
            help='Name of the interface on endpointD towards routerR (e.g. "ensD")')
    observer.add_scenario_argument(
            '--interface-RA', required=True,
            help='Name of the interface on routerR towards endpointA (e.g. "ensR3")')
    observer.add_scenario_argument(
            '--interface-RB', required=True,
            help='Name of the interface on routerR towards endpointB (e.g. "ensR3")')
    observer.add_scenario_argument(
            '--interface-LC', required=True,
            help='Name of the interface on routerL towards endpointC (e.g. "ensL3")')
    observer.add_scenario_argument(
            '--interface-LD', required=True,
            help='Name of the Interface on routerL towards endpointD (e.g. "ensL3")')
    observer.add_scenario_argument(
            '--interface-LA', required=True,
            help='Name of the interface on routerL towards endpointA (e.g. "ensL1")')
    observer.add_scenario_argument(
            '--interface-LB', required=True,
            help='Name of the interface on routerL towards endpointB (e.g. "ensL2")')
    observer.add_scenario_argument(
            '--interface-RC', required=True,
            help='Name of the interface on routerR towards endpointC (e.g. "ensR1")')
    observer.add_scenario_argument(
            '--interface-RD', required=True,
            help='Name of the interface on routerR towards endpointD (e.g. "ensR2")') 
    observer.add_scenario_argument(
            '--interface-LR', required=True,
            help='Name of the interface on routerL towards routerR (e.g. "ensL3")')
    observer.add_scenario_argument(
            '--interface-RL', required=True,
            help='Name of the interface on routerR towards routerL (e.g. "ensR3")')
    observer.add_scenario_argument(
            '--BD-file-size', required=False, type=str, default='5000M',
            help='size of the file to transmit (in bytes) for B -> D transfer. '
            'The value must be stricly higher than 1 MB')
    observer.add_scenario_argument(
            '--AC-file-size', required=False, type=str, default='10M',
            help='size of the file to transmit (in bytes) for A -> C transfer. '
            'The value must be stricly higher than 1 MB')
    observer.add_scenario_argument(
            '--delay', required=False, nargs='+', default=['10','10','10'],
            help='one way delay of each LR link (in ms)'
            'Take three int as the job is configured three times')
    observer.add_scenario_argument(
            '--loss', required=False, nargs='+', default=['0','0','0'],
            help='parameters of the loss model'
            'Take three int as the job is configured three times')
    observer.add_scenario_argument(
            '--bandwidth', required=False, nargs='+', default=['20M','10M','20M'],
            help='bandwidth of each LR link (in bytes)'
            'Take three string as the job is configured three times')
    observer.add_scenario_argument(
            '--initcwnd', required=False, type=int, default=30,
            help='initial congestion window size for connections to this destination')
    observer.add_scenario_argument(
            '--wait-delay-LR', required=False, nargs='+', default=['10','10'],
            help='First param: wait_delay between BD trafic start and first LR '
            'link bandwidth reduction. Second param: wait_delay between first LR '
            'link bandwidth reduction and second LR link bandwidth reduction')
    observer.add_scenario_argument(
            '--congestion-control', required=True,
            help='Congestion control name (e.g. "cubic"')
    observer.add_scenario_argument(
            '--server-port', required=False, default=7001,
            help='Destination port for the iperf3 traffic')
    observer.add_scenario_argument(
            '--pep', action='store_true',
            help='Enable PEPsal on routerL and routerR')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, tcp_evaluation_suite.SCENARIO_NAME)

    scenario = tcp_evaluation_suite.build(
            args.endpointA,
            args.endpointB,
            args.endpointC,
            args.endpointD,
            args.endpointC_ip,
            args.endpointD_ip,
            args.routerL,
            args.routerR,
            args.endpointA_network_ip,
            args.endpointB_network_ip,
            args.endpointC_network_ip,
            args.endpointD_network_ip,
            args.routerL_to_endpointA_ip,
            args.routerL_to_endpointB_ip,
            args.routerR_to_endpointC_ip,
            args.routerR_to_endpointD_ip,
            args.routerL_to_routerR_ip,
            args.routerR_to_routerL_ip,
            args.interface_AL,
            args.interface_BL,
            args.interface_CR,
            args.interface_DR,
            args.interface_RA,
            args.interface_RB,
            args.interface_LC,
            args.interface_LD,
            args.interface_LA,
            args.interface_LB,
            args.interface_RC,
            args.interface_RD,
            args.interface_LR,
            args.interface_RL,
            args.BD_file_size,
            args.AC_file_size,
            args.delay,
            args.loss,
            args.bandwidth,
            args.initcwnd,
            args.wait_delay_LR,
            congestion_control=args.congestion_control,
            server_port=args.server_port,
            pep=args.pep,
            post_processing_entity=args.post_processing_entity,
            scenario_name=args.scenario_name)

    scenario_id = observer.launch_and_wait(scenario)['scenario_instance_id']

    ##################################################
    # Post process download_time of iperf3 scenarios #
    ##################################################

    results = DataProcessor(observer)
    iperf3_scenarios = list(scenario.extract_function_id(iperf3=iperf3_find_client, include_subscenarios=True))

    i = 0
    #The first element is BD link as it is launched first. We don't need his metric.
    for stat in iperf3_scenarios[1:]:
        i = i + 1
        results.add_callback('download_time_'+str(i), extract_iperf_statistic, stat)
    values = results.post_processing()

    #########################
    ###### Do the plot ######
    #########################

    path = observer.args.path
    observer_file = observer.args.file

    timestamps, pts = ([v[0][0] for f,v in values.items()], [v[0][1] for k,v in values.items()])
    df = pd.DataFrame({'download_time': pts}, index=timestamps)

    for stat_name, ts_xlabel, ts_ylabel, ts_title, cdf_xlabel, cdf_ylabel, cdf_title in (
        ('download_time', 'Time (ms)', 'Download Time (s)', 'Download Time time series', 'Download Time (s)', 'CDF', 'Download Time CDF'),):

        #########################
        ######## ts plot ########
        #########################

        figure, axis = plt.subplots()
        plt.xlabel(ts_xlabel)
        plt.ylabel(ts_ylabel)
        df.plot(y=stat_name, ax=axis, title=ts_title, grid=True, legend=False, linewidth=2)
        register_figure(path, scenario_id, observer_file, 'ts')

        #########################
        ####### cdf plot ########
        #########################

        figure, axis = plt.subplots()
        plt.xlabel(cdf_xlabel)
        plt.ylabel(cdf_ylabel)
        df.plot(kind='hist', y=stat_name, ax=axis, title=cdf_title, grid=True, legend=False, histtype='step', bins=100, cumulative=1, density=True)
        register_figure(path, scenario_id, observer_file, 'cdf')

if __name__ == '__main__':
    main()
