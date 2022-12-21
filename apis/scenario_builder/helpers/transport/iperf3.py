#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2023 CNES
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
        server_ip, port, duration, num_flows, tos=None,
        mtu=None, metrics_interval=1, congestion_control=None,
        wait_finished=None, wait_launched=None, wait_delay=0):

    server = iperf3_server(
            scenario, server_entity, server_ip, port,
            metrics_interval=metrics_interval, reverse=True, exit=True,
            wait_finished=wait_finished, wait_launched=wait_launched, wait_delay=wait_delay)

    iperf3_client(
            scenario, client_entity, server_ip, port, "tcp",
            duration=duration, num_flows=num_flows, tos=tos, tcp_mtu=mtu,
            metrics_interval=metrics_interval,
            congestion_control=congestion_control,
            wait_launched=server, wait_delay=2)

    return server


def iperf3_rate_udp(
        scenario, client_entity, server_entity,
        server_ip, port, duration, num_flows=None,
        tos=None, bandwidth=None, udp_size=None, metrics_interval=1,
        wait_finished=None, wait_launched=None, wait_delay=0):

    server = iperf3_server(
            scenario, server_entity, server_ip, port,
            metrics_interval=metrics_interval, reverse=True, exit=True,
            wait_finished=wait_finished, wait_launched=wait_launched, wait_delay=wait_delay)

    iperf3_client(
            scenario, client_entity, server_ip, port,
            "udp", duration=duration, reverse=True,
            metrics_interval=metrics_interval,
            num_flows=num_flows, tos=tos,
            udp_bandwidth=bandwidth, udp_size=udp_size,
            wait_launched=server, wait_delay=2)

    return server


def iperf3_send_file_tcp(
        scenario, client_entity, server_entity,
        server_ip, port, transmitted_size, tos=None,
        mtu=None, metrics_interval=1, congestion_control=None,
        wait_finished=None, wait_launched=None, wait_delay=0):

    server = iperf3_server(
            scenario, server_entity, server_ip, port,
            exit=True, reverse=True, metrics_interval=metrics_interval,
            wait_finished=wait_finished, wait_launched=wait_launched, wait_delay=wait_delay)

    iperf3_client(
            scenario, client_entity, server_ip, port,
            "tcp", metrics_interval=metrics_interval, reverse=True,
            tos=tos, tcp_mtu=mtu, transmitted_size=transmitted_size,
            congestion_control=congestion_control,
            wait_launched=server, wait_delay=2)

    return server


def iperf3_server(
        scenario, server_entity, server_ip, port,
        metrics_interval=1, reverse=True, exit=True,
        wait_finished=None, wait_launched=None, wait_delay=0):

    server = scenario.add_function(
        'start_job_instance',
        wait_finished=wait_finished,
        wait_launched=wait_launched,
        wait_delay=wait_delay)

    server.configure(
            'iperf3',
            server_entity,
            offset=0,
            port=port,
            reverse=reverse,
            metrics_interval=metrics_interval,
            server={
                'exit': exit,
                'bind': server_ip,
            })

    return [server]


def iperf3_client(
        scenario, client_entity, server_ip, port,
        protocol, metrics_interval=1, duration=None,
        num_flows=None, tos=None, transmitted_size=None, reverse=True,
        congestion_control=None, tcp_mtu=None, udp_bandwidth=None,
        udp_size=None,
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
    clients_parameters[protocol] = {}
    if protocol == "tcp":
        if tcp_mtu is not None:
            clients_parameters['tcp']['mss'] = tcp_mtu
        if congestion_control is not None:
            clients_parameters['tcp']['cong_control'] = congestion_control
    elif protocol == "udp":
        if udp_bandwidth is not None:
            clients_parameters['udp']['bandwidth'] = str(udp_bandwidth)
        if udp_size is not None:
            clients_parameters['udp']['udp_size'] = str(udp_size)

    parameters = {
        "metrics_interval": metrics_interval,
        'port': port,
        'client': clients_parameters,
    }
    if num_flows is not None:
        parameters['num_flows'] = num_flows
    parameters['reverse'] = reverse

    client.configure('iperf3', client_entity, offset=0, **parameters)
    return [client]


def iperf3_find_server(openbach_function):
    return 'server' in openbach_function.start_job_instance['iperf3']


def iperf3_find_client(openbach_function):
    return 'client' in openbach_function.start_job_instance['iperf3']
