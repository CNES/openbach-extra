#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Joaquin MUGUERZA / <joaquin.muguerza@toulouse.viveris.com>

"""
measure_scenario_builder.py
"""

import sys
import argparse

import scenario_builder as sb

"""
Scenario:
    - launch socat on server
    - launch N socat clients
    - stop server
"""

SCENARIO_NAME = "measure time"

def main(server, client, ntimes):
    # Create the scenario
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_NAME)
    scenario.add_argument('filesize', 'The size of the file to measure')
    scenario.add_argument('dst_ip', 'The dst IP for the client')
    scenario.add_argument('port', 'The port of the server')

    # 1. Launch the socat server
    launch_server = scenario.add_function('start_job_instance')
    launch_server.configure(
            'socat', server, offset=0,
            server=True, port='$port', 
            file='$filesize', create_file=True,
            measure_time=False)
    wait_launched = [launch_server]
    wait_finished = []
    wait_delay = 20 # need big delay 'cause file copy is slow
    # 2. Launch clients
    for i in range(ntimes):
        launch_client = scenario.add_function(
                'start_job_instance',
                wait_launched=wait_launched,
                wait_finished=wait_finished,
                wait_delay=wait_delay
        )
        launch_client.configure(
                'socat', client, offset=2,
                server=False, dst_ip='$dst_ip', port='$port',
                file='$filesize', create_file=False, measure_time=True
        )
        wait_launched = []
        wait_finished = [launch_client]
        wait_delay = 1
    # Stop server
    stop_server = scenario.add_function(
            'stop_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched
    )
    stop_server.configure(launch_server)

    scenario.write('{}.json'.format(SCENARIO_NAME))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('server', metavar='server', type=str,
                        help='IP address of the server')
    parser.add_argument('client', metavar='client', type=str,
                        help='IP address of the client')
    parser.add_argument('ntimes', metavar='ntimes', type=int,
                        help='The number of times to launch the client')

    args = parser.parse_args()

    main(args.server, args.client, args.ntimes)
