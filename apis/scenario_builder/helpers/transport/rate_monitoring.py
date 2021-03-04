#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2020 CNES
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

"""Helpers of rate_monitoring job"""

from ..utils import filter_none

def rate_monitoring(
        scenario, entity, sampling_interval, chain_name, source_ip=None,
        destination_ip=None, in_interface=None, out_interface=None, 
        ### other_parser
        wait_finished=None, wait_launched=None, wait_delay=0):

    function = scenario.add_function(
           'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            source_ip=source_ip,
            destination_ip=destination_ip,
            in_interface=in_interface,
            out_interface=out_interface)

    function.configure('rate_monitoring', entity, **parameters)

    return [function]
