#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016−2019 CNES
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

""" Helpers of open_sand job """

def opensand_network_ip(scenario, entity, address_mask, tap_name = 'opensand_tap', 
        bridge_name = 'opensand_br', wait_finished = None, wait_launched = None, wait_delay = 0):

    opensand = scenario.add_function('start_job_instance',
                 wait_finished = wait_finished,
                 wait_launched = wait_launched,
                 wait_delay = wait_delay)
    opensand.configure('opensand', entity, network = {'tap_name': tap_name,
        'bridge_name': bridge_name, 'ip' : {'address_mask': address_mask}})

    return [opensand]


def opensand_network_eth(scenario, entity, interface, tap_name = 'opensand_tap',
        bridge_name = 'opensand_br', wait_finished = None, wait_launched = None, wait_delay = 0):

    opensand = scenario.add_function('start_job_instance',
                 wait_finished = wait_finished,
                 wait_launched = wait_launched,
                 wait_delay = wait_delay)
    opensand.configure('opensand', entity, network = {'tap_name': tap_name,
        'bridge_name': bridge_name, 'eth': {'interface': interface}})

    return [opensand]

def opensand_network_clear(scenario, entity, tap_name = 'opensand_tap',
        bridge_name = 'opensand_br', wait_finished = None, wait_launched = None, wait_delay = 0):

    opensand = scenario.add_function('start_job_instance',
                 wait_finished = wait_finished,
                 wait_launched = wait_launched,
                 wait_delay = wait_delay)
    opensand.configure('opensand', entity, network = {'tap_name': tap_name,
        'bridge_name' : bridge_name, 'action': 'clear'})

    return [opensand]

def opensand_run(scenario, agent_entity, entity, configuration = '/etc/opensand', 
        output_address = '127.0.0.1', logs_port = 63000, stats_port = 63001,
        binaries_directory = '/usr/bin', entity_id = None,
        emulation_address = None, interconnection_address = None, 
        wait_finished = None, wait_launched = None, wait_delay = 0):

    opensand = scenario.add_function('start_job_instance',
                 wait_finished = wait_finished,
                 wait_launched = wait_launched,
                 wait_delay = wait_delay)
    if entity == 'sat': 
        opensand.configure('opensand', agent_entity, run = { 'configuration' : configuration, 
            'output_address' : output_address, 'logs_port' : logs_port,
            'stats_port' : stats_port, 'binaries directory' : binaries_directory,
            'sat' : {'emulation_address' : emulation_address}})
    elif entity == 'gw':
        opensand.configure('opensand', agent_entity, run = { 'configuration' : configuration,
            'output_address' : output_address, 'logs_port' : logs_port,
            'stats_port' : stats_port, 'binaries directory' : binaries_directory,
            'gw' : {'id': entity_id, 'emulation_address' : emulation_address}})
    elif entity == 'gw-phy':
        opensand.configure('opensand', agent_entity, run = { 'configuration' : configuration,
            'output_address' : output_address, 'logs_port' : logs_port,
            'stats_port' : stats_port, 'binaries directory' : binaries_directory,
            'gw-phy' : {'id': entity_id, 'emulation_address' : emulation_address, 
                        'interconnection_address' : interconnection_address}})
    elif entity == 'gw-net-acc':
        opensand.configure('opensand', agent_entity, run = { 'configuration' : configuration,
            'output_address' : output_address, 'logs_port' : logs_port,
            'stats_port' : stats_port, 'binaries directory' : binaries_directory,
            'gw-net-acc' : {'id': entity_id, 'interconnection address' : interconnection_address}})
    elif entity == 'st':
        opensand.configure('opensand', agent_entity, run = { 'configuration' : configuration,
            'output_address' : output_address, 'logs_port' : logs_port,
            'stats_port' : stats_port, 'binaries directory' : binaries_directory,
            'st' : {'id': entity_id, 'emulation_address' : emulation_address}})

    return [opensand]

