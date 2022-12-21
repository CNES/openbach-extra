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

"""Helpers of outoforder_detect job"""


def outoforder_detect(
        scenario, server_entity, client_entity, server_ip,
        duration=5, transmitted_packets=None,
        server_port=61234, signal_port=61235,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'outoforder_detect', server_entity,
            server={
                'exit': True,
                'address': server_ip,
            },
            server_port=server_port,
            signal_port=signal_port)

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)

    client_parameters = {
            'server_ip': server_ip,
            'duration': duration,
    }

    if transmitted_packets:
        client_parameters['transmitted_packets'] = transmitted_packets

    parameters = {
            'client': client_parameters,
            'server_port': server_port,
            'signal_port': signal_port
    }

    client.configure('outoforder_detect', client_entity, **parameters)
    return [server]


def outoforder_server(
        scenario, server_entity, server_ip, server_port=61234, signal_port=61235,
        exit=True, wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'outoforder_detect', server_entity,
            server={
                'exit': exit,
                'address': server_ip,
                'server_port': server_port,
                'signal_port': signal_port
            })
    return [server]


def outoforder_client(
        scenario, client_entity, server_ip,
        duration=5, transmitted_packets=None,
        server_port=61234, signal_port=61235,
        wait_finished=None, wait_launched=None, wait_delay=0):
    client = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    client_parameters = {
            'server_ip': server_ip,
            'duration': duration,
    }

    if transmitted_packets:
        client_parameters['transmitted_packets'] = transmitted_packets

    parameters = {
            'client': client_parameters,
            'server_port': server_port,
            'signal_port': signal_port
    }

    client.configure('outoforder_detect', client_entity, **parameters)
    return [client]


def outoforder_find_server(openbach_function):
    return 'server' in openbach_function.start_job_instance['outoforder_detect']

def outoforder_find_client(openbach_function):
    return 'client' in openbach_function.start_job_instance['outoforder_detect']

