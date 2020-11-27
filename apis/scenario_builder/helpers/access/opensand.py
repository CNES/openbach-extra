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

""" Helpers of opensand job """


def opensand_run(
        scenario, agent_entity, entity, configuration=None,
        output_address=None, logs_port=None, stats_port=None,
        binaries_directory=None, entity_id=None, tap_name=None,
        emulation_address=None, interconnection_address=None, 
        wait_finished=None, wait_launched=None, wait_delay=0):

    opensand = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    run = {
            entity: {'id': entity_id, 'emulation_address': emulation_address},
    }

    if configuration:
        run['configuration'] = configuration
    if output_address:
        run['output_address'] = output_address
    if logs_port:
        run['logs_port'] = logs_port
    if stats_port:
        run['stats_port'] = stats_port
    if binaries_directory:
        run['binaries_directory'] = binaries_directory

    if entity == 'sat': 
        del run[entity]['id']
    elif entity == 'gw-phy':
        run[entity]['interconnection_address'] = interconnection_address
    elif entity == 'gw-net-acc':
        del run[entity]['emulation_address']
        run[entity]['interconnection address'] = interconnection_address
    if entity in ['gw', 'gw-net-acc', 'st']:
        run[entity]['tap_name'] = tap_name
    opensand.configure('opensand', agent_entity, **run)

    return [opensand]


def opensand_find_sat(openbach_function):
    return 'sat' in openbach_function.start_job_instance['opensand']


def opensand_find_st(openbach_function):
    return 'st' in openbach_function.start_job_instance['opensand']


def opensand_find_gw(openbach_function):
    return 'gw' in openbach_function.start_job_instance['opensand']


def opensand_find_gw_net_acc(openbach_function):
    return 'gw-net-acc' in openbach_function.start_job_instance['opensand']


def opensand_find_gw_phy(openbach_function):
    return 'gw-phy' in openbach_function.start_job_instance['opensand']
