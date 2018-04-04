#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: David PRADAS / <david.pradas@toulouse.viveris.com>

"""
rate_udp.py
"""

import sys
import argparse

import scenario_builder as sb

"""
Scenario:
"""

SCENARIO_NAME = "rate_udp"

def main(server, client, rate_min, rate_max, rate_steps):
    # Create the scenario
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_NAME)
    #scenario.add_argument('client', 'The client entity')
    #scenario.add_argument('server', 'The server entity')
    scenario.add_argument('dst_ip', 'The IP of the server')
    scenario.add_argument('port', 'The port of the server')
    scenario.add_argument('com_port', 'The port of nuttcp server for signalling')
    scenario.add_argument('ntimes', 'The number of tests to perform')
    scenario.add_argument('duration', 'The duration of each test (sec.)')
    #scenario.add_argument('parallel_flows', 'A list with the number of parallel flows to test')
    #scenario.add_argument('mtu_sizes', 'A list with the mtu sizes to test')
    #scenario.add_argument('tos_values', 'A list the ToS values to test ')

    wait_launched = []
    wait_finished = []
    wait_delay = 1 
    # 2. Launch clients
    for rate in range(rate_min, rate_max, rate_steps):
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
            receiver=False, udp=True , duration='$duration', iterations='$ntimes', rate_limit=rate
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
    parser.add_argument('--rate_min', metavar='rate_min', 
                        type=int, help='The minimum rate (b/s) to test in udp')
    parser.add_argument('--rate_max', metavar='rate_max', 
                        type=int, help='The maximum rate (n/s) to test in udp')
    parser.add_argument('--rate_steps', metavar='rate_steps', 
                        type=int, help='The rate granularity between one test and the next one')


    args = parser.parse_args()
    main(args.server, args.client, args.rate_min, args.rate_max, args.rate_steps)

