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

""" Helpers of web_browsing_qoe job """


def web_browsing_qoe(
        scenario, entity, duration, nb_runs, nb_parallel_runs,
        no_compression=False, proxy_address=None, proxy_port=None, urls=None,
        wait_finished=None, wait_launched=None, wait_delay=0):

    launch_browsing = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    browsing_parameters = {
            'nb_runs': nb_runs,
            'nb_parallel_runs': nb_parallel_runs,
            'no_compression': no_compression
    }

    if proxy_port is not None :
        browsing_parameters['proxy_port'] = proxy_port
    if proxy_address is not None:
        browsing_parameters['proxy_address'] = proxy_address
    if urls is not None:
        browsing_parameters['urls'] = urls

    launch_browsing.configure('web_browsing_qoe', entity, offset=0, **browsing_parameters)

    if duration:
        stop_launch_browsing = scenario.add_function(
                'stop_job_instance',
                wait_launched=[launch_browsing],
                wait_delay=duration)
        stop_launch_browsing.configure(launch_browsing)

    return [launch_browsing]
