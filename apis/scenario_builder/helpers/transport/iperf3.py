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

"""Helpers of iperf3 job"""


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
            'iperf3', server_entity,
            offset=0,
            num_flows=num_flows,
            port=port,
            interval=1.0,
            server={
                'exit': True,
                'bind': server_ip,
            })

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', client_entity,
            offset=0,
            num_flows=num_flows,
            port=port,
            client={
                'server_ip': server_ip,
                'duration_time': duration,
                'tos': str(tos),
                'tcp': {'mss': str(mtu)},
            })

    return [server]


def iperf3_rate_udp(
        scenario, client_entity, server_entity,
        server_ip, port, num_flows, duration, tos, bandwidth,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'iperf3', server_entity,
            offset=0,
            num_flows=num_flows,
            port=port,
            interval=1.0,
            server={
                'exit': True,
                'bind': server_ip,
            })

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', client_entity,
            offset=0,
            num_flows=num_flows,
            port=port,
            client={
                'server_ip': server_ip,
                'duration_time': duration,
                'tos': str(tos),
                'udp': {'bandwidth': str(bandwidth)},
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
            'iperf3', server_entity,
            offset=0,
            port=port,
            server={
                'exit': True,
                'bind': server_ip,
            })

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', client_entity,
            offset=0,
            port=port,
            client={
                'server_ip': server_ip,
                'transmitted_size': transmitted_size,
                'tos': str(tos),
                'tcp': {'mss': str(mtu)},
            })

    return [server]


def iperf3_server(
        scenario, server_entity, server_ip, port, exit=True,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'iperf3', server_entity,
            offset=0,
            port=port,
            server={
                'exit': exit,
                'bind': server_ip,
            })
    return [server]


def iperf3_client(
        scenario, client_entity, server_ip, port,
        duration=None, num_flows=None, tos=None,
        transmitted_size=None, tcp_mtu=None, udp_bandwidth=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    client = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    clients_parameters = {
            'server_ip': server_ip,
    }
    if tos is not None:
        clients_parameters['tos'] = str(tos)
    if transmitted_size is not None:
        clients_parameters['transmitted_size'] = transmitted_size
    if duration is not None:
        clients_parameters['duration_time'] = duration
    if tcp_mtu is not None:
        clients_parameters['tcp'] = {'mss': str(tcp_mtu)}
    if udp_bandwidth is not None:
        clients_parameters['udp'] = {'bandwidth': str(bandwidth)}
    parameters = {
            'port': port,
            'client': clients_parameters,
    }
    if num_flows is not None:
        parameters['num_flows'] = num_flows

    client.configure('iperf3', client_entity, offset=0, **parameters)
    return [client]


def iperf3_find_server(openbach_function):
    return 'server' in openbach_function.start_job_instance['iperf3']
