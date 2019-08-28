#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016−2019 CNES
#
#
#   This file is part of the OpenBACH testbed.
#
#
#   OpenBACH is a free software : you can redistribute it and/or modify it under
#   the terms of the GNU General Public License as published by the Free Software
#   Foundation, either version 3 of the License, or (at your option) any later
#   version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
#   details.
#
#   You should have received a copy of the GNU General Public License along with
#   this program. If not, see http://www.gnu.org/licenses/.

""" Helpers of iperf3 job """

def iperf3_rate_tcp(
        scenario, client_entity, server_entity,
        server_ip, port, duration, num_flows, tos, mtu,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'iperf3', server_entity, offset=0,
            num_flows=num_flows, port=port,
            interval=1.0, server={'exit':True, 'bind':server_ip})

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', client_entity, offset=0,
             num_flows=num_flows, port=port,
             client={
                'server_ip': server_ip,
                'duration_time': duration,
                'tos': '{0}'.format(tos),
                'tcp': {'mss':'{0}'.format(mtu)},
            })

    return [server]

def iperf3_rate_udp(
        scenario, client_entity, server_entity,
        server_ip, port, num_flows, duration,
        tos, bandwidth,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'iperf3', server_entity, offset=0,
            num_flows=num_flows, port=port,
            interval=1.0, server={'exit':True, 'bind':server_ip})

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', client_entity, offset=0,
             num_flows=num_flows, port=port,
             client={
                'server_ip': server_ip,
                'duration_time': duration,
                'tos': '{0}'.format(tos),
                'udp': {'bandwidth':'{0}'.format(bandwidth)},
            })

    return [server]


def iperf3_send_file_tcp(
        scenario, client_entity, server_entity,
        server_ip, port, transmitted_size, tos, mtu,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'iperf3', server_entity, offset=0,
            port=port, server={'exit': True, 'bind':server_ip})

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', client_entity, offset=0,
            port=port, client={
                'server_ip': server_ip,
                'transmitted_size': transmitted_size,
                'tos': '{0}'.format(tos),
                'tcp': {'mss':'{0}'.format(mtu)},
            })

    return [server]
