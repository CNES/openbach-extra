#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016−2020 CNES
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

""" Helpers of the job tcpdump """

from ..utils import filter_none


def tcpdump_capture_only(
      scenario, entity, iface, capture_file, src_ip=None, dst_ip=None, 
      src_port=None, dst_port=None, proto=None, duration=None,
      wait_finished=None, wait_launched=None, wait_delay=0):
    f_start_capture = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            proto=proto)
    parameters['capture'] = filter_none(        
            iface=iface,
            capture_file=capture_file, 
            duration=duration)
    parameters['capture']['capture_only']={}
    f_start_capture.configure(
            'tcpdump', entity,
            **parameters)

    return [f_start_capture]


def tcpdump_capture_analyze(
      scenario, entity, iface, capture_file, src_ip=None, dst_ip=None, 
      src_port=None, dst_port=None, proto=None, duration=None, metrics_interval=None,
      wait_finished=None, wait_launched=None, wait_delay=0):
    f_start_capture_analyze = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            proto=proto)
    parameters['capture'] = filter_none(        
            iface=iface,
            capture_file=capture_file, 
            duration=duration)
    parameters['capture']['capture_analyze']= filter_none(
             metrics_interval=metrics_interval)
    f_start_capture_analyze.configure(
            'tcpdump', entity,
            **parameters)

    return [f_start_capture_analyze]


def tcpdump_analyze(
        scenario, entity, capture_file, src_ip=None, dst_ip=None, 
        src_port=None, dst_port=None, proto=None, metrics_interval=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    f_start_analyze = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            proto=proto)
    parameters['analyze'] = filter_none(
            capture_file=capture_file,        
            metrics_interval=metrics_interval)
    f_start_analyze.configure(
            'tcpdump', entity,
            **parameters)

    return [f_start_analyze]


def tcpdump_find_analyze(openbach_function):
    return 'analyze' in openbach_function.start_job_instance['tcpdump']


