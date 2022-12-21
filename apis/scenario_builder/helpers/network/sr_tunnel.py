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

""" Helpers of sr_tunnel job """

from ..utils import filter_none


def create_sr_tunnel(
        scenario, server_entity, client_entity, server_ip, server_tun_ip, client_tun_ip, server_port=None,
        trace=None, server_drop=None, client_drop=None, server_burst=None, client_burst=None,
        wait_finished=None, wait_launched=None, wait_delay=0):

    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    server_params = filter_none(
            tun_ip=server_tun_ip,
            trace=trace,
            drop=server_drop,
            burst=server_burst)

    server_params['server'] = {'port': server_port} if server_port is not None else {}

    server.configure(
            'sr_tunnel',
            server_entity,
            **server_params)

    client = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=[server],
            wait_delay=2)

    client_params = filter_none(
            tun_ip=client_tun_ip,
            trace=trace,
            drop=client_drop,
            burst=client_burst)

    client_subparams = filter_none(
            server_ip=server_ip,
            server_port=server_port)

    client_params['client'] = client_subparams
    client.configure('sr_tunnel', client_entity, **client_params)

    return [server]


def init_sr_server(
        scenario, server_entity, server_tun_ip, server_port=None, trace=None,
        drop=None, burst=None, wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            tun_ip=server_tun_ip,
            trace=trace,
            drop=drop,
            burst=burst)

    if server_port is not None:
        parameters['client'] = {'port': server_port}

    server.configure(
            'sr_tunnel',
            server_entity,
            **parameters)

    return [server]


def init_sr_client(
        scenario, client_entity, client_tun_ip, server_ip, server_port=None, trace=None,
        drop=None, burst=None, wait_finished=None, wait_launched=None, wait_delay=0):
    client = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            tun_ip=server_tun_ip,
            trace=trace,
            drop=drop,
            burst=burst)

    client_params = filte_none(
            server_ip=server_ip,
            server_port=server_port)

    parameters['client'] = client_params
    client.configure('sr_tunnel', client_entity, **parameters)

    return [client]


def sr_tunnel_find_server(openbach_function):
    return 'server' in openbach_function.start_job_instance['sr_tunnel']

def sr_tunnel_find_client(openbach_function):
    return 'client' in openbach_function.start_job_instance['sr_tunnel']


