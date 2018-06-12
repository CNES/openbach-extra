#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import scenario_builder as sb


def main(client, server):

    # Create the scenario
    scenario = sb.Scenario('Delay metrology scenario (fping, hping, owping)', 'Comparison of 3 RTTs')
    scenario.add_argument('ip_dst', 'Target of the pings and server ip adress')

    # Job 'owamp-server'
    owamp_server = scenario.add_function('start_job_instance')
    owamp_server.configure('owamp-server', server, offset=0,
                           server_address='$ip_dst')

    # Job 'owamp-client'
    owamp_client = scenario.add_function('start_job_instance',
                                         wait_launched=[owamp_server],
                                         wait_delay=5)
    owamp_client.configure('owamp-client', client, offset=0,
                           destination_address='$ip_dst')
    # Job 'hping'
    hping = scenario.add_function('start_job_instance',
                                  wait_launched=[owamp_client])
    hping.configure('hping', client, destination_ip='$ip_dst')

    # Job 'fping'
    fping = scenario.add_function('start_job_instance',
                                  wait_launched=[owamp_client])
    fping.configure('fping', client, offset=0,
                    destination_ip='$ip_dst')

    # Stop pings and owamp server
    stop_pings = scenario.add_function('stop_job_instance',
                                       wait_finished=[owamp_client])
    stop_pings.configure(hping, fping, owamp_server)

    # Write the scenario in a file in a json format
    scenario.write('owdelay_metrology.json')


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
