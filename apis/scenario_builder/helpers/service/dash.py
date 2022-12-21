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

""" Helpers of DASH jobs """


def dash_client_and_server(
        scenario, server_entity, client_entity, server_ip, duration,
        protocol, tornado_port,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure('apache2', server_entity, offset=0)

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'dashjs_client', client_entity, offset=0,
            dst_ip=server_ip, protocol=protocol,
            tornado_port=tornado_port, duration=duration)

    stopper = scenario.add_function(
            'stop_job_instance',
            wait_finished=[client],
            wait_delay=5)
    stopper.configure(server)

    return [server]


def dash_client(
        scenario, client_entity, server_ip, duration,
        protocol, tornado_port,
        wait_finished=None, wait_launched=None, wait_delay=0):
    client = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    client.configure(
            'dashjs_client', client_entity, offset=0,
            dst_ip=server_ip, protocol=protocol,
            tornado_port=tornado_port, duration=duration)

    return [client]