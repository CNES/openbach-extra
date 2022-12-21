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

"""Helpers of twinkle_voip job"""


def twinkle_voip(
        scenario, server_entity, client_entity, local_ip, remote_ip, duration,
        wait_finished=None, wait_launched=None, wait_delay=0):
    launch_server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    launch_server.configure(
            'twinkle_voip', server_entity, offset=0,
            local_ip=local_ip,
            server=True)

    launch_client = scenario.add_function(
            'start_job_instance',
            wait_launched=[launch_server],
            wait_delay=5)
    launch_client.configure(
            'twinkle_voip', client_entity, offset=0,
            local_ip=local_ip,
            remote_ip=remote_ip,
            length=duration)

    stop_server = scenario.add_function(
            'stop_job_instance',
            wait_finished=[launch_client])
    stop_server.configure(launch_server)

    return [launch_server]
