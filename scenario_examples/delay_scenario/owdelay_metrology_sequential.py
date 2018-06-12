#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import scenario_builder as sb


def main(client, server):

    # Create the scenario
    scenario = sb.Scenario('Sequential delay metrology scenario (fping, hping, owping)',
                           'Comparison of 3 RTTs at different times')
    scenario.add_argument('ip_dst', 'Target of the pings and server ip adress')

    # Job 'hping'
    hping = scenario.add_function('start_job_instance')
    hping.configure('hping', client, destination_ip='$ip_dst')

    # Stop hping
    stop_hping = scenario.add_function('stop_job_instance',
                                       wait_launched=[hping],
                                       wait_delay=60)
    stop_hping.configure(hping)

    # Job 'fping'
    fping = scenario.add_function('start_job_instance',
                                  wait_finished=[hping])
    fping.configure('fping', client, offset=0,
                    destination_ip='$ip_dst')

    # Stop fping
    stop_fping = scenario.add_function('stop_job_instance',
                                       wait_launched=[fping],
                                       wait_delay=60)
    stop_fping.configure(fping)

    # Job 'owamp-server'
    owamp_server = scenario.add_function('start_job_instance',
                                         wait_finished=[fping])
    owamp_server.configure('owamp-server', server, offset=0,
                           server_address='$ip_dst')

    # Job 'owamp-client'
    owamp_client = scenario.add_function('start_job_instance',
                                         wait_launched=[owamp_server],
                                         wait_delay=5)
    owamp_client.configure('owamp-client', client, offset=0,
                           destination_address='$ip_dst')

    # Stop owamp server
    stop_owamp = scenario.add_function('stop_job_instance',
                                       wait_finished=[owamp_client])
    stop_owamp.configure(owamp_server)

    # Write the scenario in a file in a json format
    scenario.write('owdelay_metrology_sequential.json')


if __name__ == '__main__':
    # Define Usage
    parser = argparse.ArgumentParser(description='',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('client', metavar='client', type=str,
                        help='Entity name from which the pings are launched')
    parser.add_argument('server', metavar='server', type=str,
                        help='Entity name to which the pings are launched')

    # get args
    args = parser.parse_args()
    client = args.client
    server = args.server

    main(client, server)

