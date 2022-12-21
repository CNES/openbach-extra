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

""" Helpers of ip_link job """


def ip_link_set(
        scenario, entity, name, state=None,
        arp=None, dynamic=None, multicast=None,
        address=None, broadcast=None, mtu=None,
        txqueuelen=None, netns=None, master=None,
        nomaster=None, type=None,
        wait_finished=None, wait_launched=None, wait_delay=0,
        **type_args):
    ip_link = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = {'device': name}
    if state is not None:
        parameters['state'] = state
    if arp is not None:
        parameters['arp'] = arp
    if dynamic is not None:
        parameters['dynamic'] = dynamic
    if multicast is not None:
        parameters['multicast'] = multicast
    if address is not None:
        parameters['address'] = address
    if broadcast is not None:
        parameters['broadcast'] = broadcast
    if mtu is not None:
        parameters['mtu'] = mtu
    if txqueuelen is not None:
        parameters['txqueuelen'] = txqueuelen
    if master is not None:
        parameters['master'] = master
    if nomaster:
        parameters['nomaster'] = nomaster
    if type is not None:
        parameters[type] = type_args

    ip_link.configure('ip_link', entity, set=parameters)

    return [ip_link]


def ip_link_add(
        scenario, entity, name,
        link=None, address=None, broadcast=None,
        mtu=None, txqueuelen=None, type='dummy',
        wait_finished=None, wait_launched=None, wait_delay=0,
        **type_args):
    ip_link = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = {'name': name, type: type_args}
    if link is not None:
        parameters['link'] = link
    if address is not None:
        parameters['address'] = address
    if broadcast is not None:
        parameters['broadcast'] = broadcast
    if mtu is not None:
        parameters['mtu'] = mtu
    if txqueuelen is not None:
        parameters['txqueuelen'] = txqueuelen

    ip_link.configure('ip_link', entity, add=parameters)

    return [ip_link]


def ip_link_del(
        scenario, entity, name, type=None,
        wait_finished=None, wait_launched=None,
        wait_delay=0, **type_args):
    ip_link = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = {'device': name}
    if type is not None:
        parameters[type] = type_args

    ip_link.configure('ip_link', entity, delete=parameters)

    return [ip_link]
