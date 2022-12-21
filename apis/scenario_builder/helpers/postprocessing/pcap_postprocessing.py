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

""" Helpers of the job pcap_postprocessing """

from ..utils import filter_none


def pcap_postprocessing_one_file(
        scenario, entity, capture_file, src_ip=None, dst_ip=None, 
        src_port=None, dst_port=None, proto=None, metrics_interval=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    f_start_analyze = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            capture_file=capture_file,        
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            proto=proto,
            stats_one_file={
                'metrics_interval': metrics_interval
            })

    f_start_analyze.configure(
            'pcap_postprocessing', entity, **parameters)

def pcap_postprocessing_gilbert_elliot(
        scenario, entity, capture_file, second_capture_file,
        src_ip=None, dst_ip=None, src_port=None, dst_port=None, proto=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    f_start_analyze = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            capture_file=capture_file,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            proto=proto,
            gilbert_elliot={
                'second_capture_file': second_capture_file
            })

    f_start_analyze.configure(
            'pcap_postprocessing', entity, **parameters)

    return [f_start_analyze]


