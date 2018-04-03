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

SCENARIO_NAME = "rate_scenario"

def main(server, client, jobs, parallel_flows, mtu_sizes, tos_values):
    # Create the scenario
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_NAME)
    #scenario.add_argument('client', 'The client entity')
    #scenario.add_argument('server', 'The server entity')
    scenario.add_argument('dst_ip', 'The IP of the server')
    scenario.add_argument('port', 'The port of the server')
    scenario.add_argument('com_port', 'The port of nuttcp server for signalling')
    scenario.add_argument('ntimes', 'The number of tests to perform')
    scenario.add_argument('duration', 'The duration of each test (sec.)')
    scenario.add_argument('tcp_eq_time', 'The elasped time after which we begin to consider the rate measures for TCP mean calculation')
    #scenario.add_argument('parallel_flows', 'A list with the number of parallel flows to test')
    #scenario.add_argument('mtu_sizes', 'A list with the mtu sizes to test')
    #scenario.add_argument('tos_values', 'A list the ToS values to test ')

    wait_launched = []
    wait_finished = []
    wait_delay = 1 
    # 2. Launch clients
    for jobname in jobs:
        for pflows in parallel_flows:
            for mtu in mtu_sizes:
                for tos in tos_values:
                    print("job {0} nflows {1} mtu {2} tos 0{3}".format(jobname, pflows, mtu, tos))
                    if jobname == 'iperf3':
                        launch_iperfserver = scenario.add_function(
                            'start_job_instance',
                            wait_launched=wait_launched,
                            wait_finished=wait_finished,
                            wait_delay=wait_delay
                        )
                        launch_iperfserver.configure(
                             'iperf3', server, offset=0,
                             server_mode=True, port='$port', num_flows=pflows,
                             exit=True, iterations='$ntimes', rate_compute_time='$tcp_eq_time'
                        )
                        wait_launched = [launch_iperfserver]
                        wait_finished = []
                        wait_delay = 2
                       
                        launch_iperfclient = scenario.add_function(
                            'start_job_instance',
                            wait_launched=wait_launched,
                            wait_finished=wait_finished,
                            wait_delay=wait_delay
                        )
                        launch_iperfclient.configure(
                            'iperf3', client, offset=0,
                            server_mode=False, client_mode_server_ip='$dst_ip', port='$port',
                            time='$duration', num_flows=pflows, mss=mtu-40, tos=tos, iterations='$ntimes'
                        )
                        wait_launched = []
                        wait_finished = [launch_iperfclient, launch_iperfserver]
                        wait_delay = 2
                    elif jobname == 'nuttcp':
                        launch_nuttcpserver = scenario.add_function(
                            'start_job_instance',
                            wait_launched=wait_launched,
                            wait_finished=wait_finished,
                            wait_delay=wait_delay
                        )
                        launch_nuttcpserver.configure(
                            'nuttcp', server, offset=0,
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
                            'nuttcp', client, offset=0,
                            server_mode=False, server_ip='$dst_ip', command_port='$com_port', port='$port',
                            receiver=False, dscp='{0}'.format(tos), mss=mtu-40,
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
    scenario.write('{}.json'.format(SCENARIO_NAME))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('server', metavar='server', type=str,
                       help='IP address of the server')
    parser.add_argument('client', metavar='client', type=str,
                        help='IP address of the client')
    #parser.add_argument('dst_ip', metavar='dst_ip', type=str,
    #                    help='The IP of the server')
    #parser.add_argument('port', metavar='port', type=str,
    #                    help='The port of the server')
    #parser.add_argument('duration', metavar='duration', type=int,
    #                    help='The duration of each test (sec.)')
    parser.add_argument('--jobs', metavar='jobs', type=str, nargs='+',
                        help='The jobs to test (iperf3, nuttcp)')
    
    parser.add_argument('--parallel_flows', metavar='parallel_flows', 
                        type=int, nargs="+", 
                        help='A list with the number of parallel flows to launch')

    parser.add_argument('--mtu_sizes', metavar='mtu_sizes', 
                        type=int, nargs="+", 
                        help='A list with the mtu sizes to test')

    parser.add_argument('--tos_values', metavar='tos_values', 
                        type=str, nargs="+", 
                        help='A list wit the ToS values to test')

    args = parser.parse_args()
    main(args.server, args.client, args.jobs, args.parallel_flows, args.mtu_sizes, args.tos_values)
    #main(args.server, args.client, args.dst_ip, args.port, args.ntimes, args.duration, args.parallel_flows, args.mtu_sizes, args.tos_values)

