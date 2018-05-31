#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: David PRADAS / <david.pradas@toulouse.viveris.com>

"""
rate_scenario_builder.py
"""

import sys
import argparse

import scenario_builder as sb

"""
Scenario:
"""

def main(scenario_name, server, client, jobs, parallel_flows, mtu_sizes, tos_values, window_sizes):
    # Create the scenario
    scenario = sb.Scenario(scenario_name, scenario_name)
    scenario.add_argument('dst_ip', 'The IP of the server')
    scenario.add_argument('port', 'The port of the server')
    if "nuttcp" in jobs:
        scenario.add_argument('com_port', 'The port of nuttcp server for signalling')
    scenario.add_argument('ntimes', 'The number of tests to perform')
    scenario.add_argument('duration', 'The duration of each test (sec.)')
    scenario.add_argument('tcp_eq_time', 'The elasped time after which we begin to consider the rate measures for TCP mean calculation')

    wait_launched = []
    wait_finished = []
    wait_delay = 1 
    # 2. Launch clients
    for jobname in jobs:
        for pflows in parallel_flows:
            for mtu in mtu_sizes:
                for tos in tos_values:
                    for win in window_sizes: 
                        print('Test with job {0}, number of flows {1}, mtu size {2}, tos'
                              '0{3} and window size {4}'.format(jobname, pflows,
                                                                mtu, tos, win))
                        if jobname == 'iperf3':
                            if win != None:
                                win = '{0}K'.format(win)
                            launch_iperf3server = scenario.add_function(
                                'start_job_instance',
                                wait_launched=wait_launched,
                                wait_finished=wait_finished,
                                wait_delay=wait_delay
                            )
                            launch_iperf3server.configure(
                                 jobname, server, offset=0,
                                 server_mode=True, port='$port', num_flows=pflows,
                                 exit=True, iterations='$ntimes', rate_compute_time='$tcp_eq_time'
                            )
                            wait_launched = [launch_iperf3server]
                            wait_finished = []
                            wait_delay = 2
                           
                            launch_iperf3client = scenario.add_function(
                                'start_job_instance',
                                wait_launched=wait_launched,
                                wait_finished=wait_finished,
                                wait_delay=wait_delay
                            )
                            launch_iperf3client.configure(
                                jobname, client, offset=0,
                                server_mode=False,
                                client_mode_server_ip='$dst_ip', port='$port',
                                window_size='{0}K'.format(win),
                                time='$duration', num_flows=pflows, mss=mtu-40, tos=tos, iterations='$ntimes'
                            )
                            wait_launched = []
                            wait_finished = [launch_iperf3client, launch_iperf3server]
                            wait_delay = 2
                            
#                         elif jobname == 'iperf':
#                            launch_iperfserver = scenario.add_function(
#                                'start_job_instance',
#                                wait_launched=wait_launched,
#                                wait_finished=wait_finished,
#                                wait_delay=wait_delay
#                            )
#                            if win != 0:
#                                 launch_iperfserver.configure(jobname, server, offset=0,
#                                     server_mode=True, port='$port',
#                                     num_flows=pflows, window_size=win,
#                                     iterations='$ntimes', rate_compute_time='$tcp_eq_time'
#                                 )
#                            else:
#                                 launch_iperfserver.configure(jobname, server, offset=0,
#                                     server_mode=True, port='$port',
#                                     num_flows=pflows, 
#                                     iterations='$ntimes', rate_compute_time='$tcp_eq_time'
#                                 )
#                                
#                            wait_launched = [launch_iperfserver]
#                            wait_finished = []
#                            wait_delay = 2
#                           
#                            launch_iperfclient = scenario.add_function(
#                                'start_job_instance',
#                                wait_launched=wait_launched,
#                                wait_finished=wait_finished,
#                                wait_delay=wait_delay
#                            )
#                            if win != 0:
#                                launch_iperfclient.configure(
#                                    jobname, client, offset=0,
#                                    server_mode=False,
#                                    client_mode_server_ip='$dst_ip', port='$port',
#                                    window_size='{0}K'.format(win),
#                                    time='$duration', num_flows=pflows, mss=mtu-40, tos=tos, iterations='$ntimes'
#                                )
#                            else:
#                                launch_iperfclient.configure(
#                                    jobname, client, offset=0,
#                                    server_mode=False,
#                                    client_mode_server_ip='$dst_ip', port='$port',
#                                    time='$duration', num_flows=pflows, mss=mtu-40, tos=tos, iterations='$ntimes'
#                                )
#                                
#                            wait_launched = []
#                            wait_finished = [launch_iperfclient, launch_iperfserver]
#                            wait_delay = 2

                        elif jobname == 'nuttcp':
                            launch_nuttcpserver = scenario.add_function(
                                'start_job_instance',
                                wait_launched=wait_launched,
                                wait_finished=wait_finished,
                                wait_delay=wait_delay
                            )
                            launch_nuttcpserver.configure(
                                jobname, server, offset=0,
                                server_mode=True, command_port='$com_port'
                            )
                            wait_launched = [launch_nuttcpserver]
                            wait_finished = []
                            wait_delay = 2
                               
                               
                            launch_nuttcpclient = scenario.add_function(
                                'start_job_instance',
                                wait_launched=wait_launched,
                                wait_finished=wait_finished,
                                wait_delay=wait_delay
                            )
                            launch_nuttcpclient.configure(
                                jobname, client, offset=0,
                                server_mode=False, server_ip='$dst_ip', command_port='$com_port', port='$port',
                                receiver=False, dscp='{0}'.format(tos), mss=mtu-40, buffer_size=win,
                                duration='$duration', n_streams=pflows, iterations='$ntimes', rate_compute_time='$tcp_eq_time'
                            )
                            wait_launched = []
                            wait_finished = [launch_nuttcpclient]
                            wait_delay = 2
                            stop_nuttcpserver = scenario.add_function(
                                 'stop_job_instance',
                                 wait_finished=wait_finished,
                                 wait_launched=wait_launched
                            )
                            stop_nuttcpserver.configure(launch_nuttcpserver)
                            wait_finished = [launch_nuttcpserver]
    scenario.write('{}.json'.format(scenario_name))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('scenario_name', metavar='scenario_name', type=str,
                        help='The name of the scenario (.json output file name)')
    parser.add_argument('server', metavar='server', type=str,
                        help='OpenBACH entity name of the server')
    parser.add_argument('client', metavar='client', type=str,
                        help='OpenBACH entity name of the client')
    parser.add_argument('jobs', type=str, nargs='+',
                        help='The list of job names to test (iperf3, nuttcp)')
    parser.add_argument('--parallel_flows', metavar='parallel_flows', 
                        type=int, nargs="+", default=[1],
                        help='A list with the number of parallel flows to launch')
    parser.add_argument('--mtu_sizes', metavar='mtu_sizes', 
                        type=int, nargs="+", default=[1400],
                        help='A list with the mtu sizes to test')
    parser.add_argument('--tos_values', metavar='tos_values', 
                        type=str, nargs="+", default=["0x00"],
                        help='A list wit the ToS values to test')
    parser.add_argument('--window_sizes', metavar='window_size', 
                        type=int, nargs="+", default=[0], 
                        help='Socket buffer sizes (in KB). For TCP, this sets '
                        'the TCP window size (0 means not specified)')

    args = parser.parse_args()
    main(args.scenario_name, args.server, args.client, args.jobs, args.parallel_flows, args.mtu_sizes, args.tos_values, args.window_sizes)

