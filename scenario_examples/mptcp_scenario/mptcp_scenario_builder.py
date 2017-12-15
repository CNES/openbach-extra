#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Joaquin MUGUERZA / <joaquin.muguerza@toulouse.viveris.com>

"""
mptcp_scenario_builder.py
"""

import sys
import argparse

import scenario_builder as sb

"""
Scenario:
    - configure opensand
    - configure terrestrial link
    - configure routing
    - configure mptcp
    - start opensand
    - launch measurements
    - stop opensand
"""

SCENARIO_NAME = "mptcp"
FILESIZES = ['1M', '5M']

def main(port, dst_ip):
    # Create the scenario
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_NAME)

    # 1. Launch scenario that configures opensand
    config_opensand = scenario.add_function('start_scenario_instance')
    config_opensand.configure('configure opensand')
    
    # 2. Launch scenario that configures terrestrial link
    config_terr = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[config_opensand])
    config_terr.configure('configure terrestrial link')

    # 3. Launch scenario that configures routing
    config_routing = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[config_terr])
    config_routing.configure('configure routing')

    # 4. Launch scenario that configures mptcp
    config_mptcp = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[config_routing])
    config_mptcp.configure('configure mptcp')

    # 5. Launch scenario that starts opensand
    launch_opensand = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[config_mptcp])
    launch_opensand.configure('start opensand')

    # 6. Launch measurements
    wait_finished = []
    wait_launched = [config_opensand]
    wait_delay = 30
    for filesize in FILESIZES:
        measure_time = scenario.add_function(
                'start_scenario_instance',
                wait_launched=wait_launched,
                wait_finished=wait_finished,
                wait_delay=wait_delay
        )
        measure_time.configure(
                'measure time',
                filesize=filesize,
                dst_ip=dst_ip,
                port=port
        )
        wait_launched = []
        wait_finished = [ measure_time ]
        wait_delay = 1

    # 7. Stop opensand
    stop_opensand = scenario.add_function(
            'stop_scenario_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay
    )
    stop_opensand.configure(launch_opensand)

    scenario.write('{}.json'.format(SCENARIO_NAME))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('port', metavar='port', type=int,
                        help='TCP port number')
    parser.add_argument('dst_ip', metavar='dst_ip', type=str,
                        help='The destination IP')

    args = parser.parse_args()

    main(args.port, args.dst_ip)
