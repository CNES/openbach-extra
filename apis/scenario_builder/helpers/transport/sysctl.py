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

"""Helpers of sysctl job"""



def sysctl_configure_tcp_congestion_control(
        scenario, entity, congestion_control,
        wait_finished=None, wait_launched=None, wait_delay=0):
    return sysctl(
            scenario, entity,
            'net.ipv4.tcp_congestion_control', congestion_control,
            wait_finished, wait_launched, wait_delay)


def sysctl_configure_ip_forwarding(
        scenario, entity, interface=None, enable=True, version=4,
        wait_finished=None, wait_launched=None, wait_delay=0):
    if interface is None:
        parameter = 'net.ipv{}.ip_forward'.format(version)
    else:
        parameter = 'net.ipv{}.conf.{}.forwarding'.format(version, interface)

    function = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    function.configure('sysctl', entity, parameter=parameter, value=int(enable))
    return [function]


def sysctl(
        scenario, entity, parameter_name, parameter_value,
        wait_finished=None, wait_launched=None, wait_delay=0):
    function = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    function.configure(
            'sysctl', entity,
            parameter=parameter_name,
            value=parameter_value)

    return [function]
