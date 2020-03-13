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

import itertools

from ..network.ip_address import ip_address
from ..network.ip_route import ip_route
from ..admin.command_shell import command_shell

def opensand_network_ip(
        scenario, entity, address_mask, tap_name=None, bridge_name=None,
        wait_finished=None, wait_launched=None, wait_delay=0):

    opensand = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    network = {'ip': {'address_mask': address_mask}}
    if tap_name:
        network['tap_name'] = tap_name
    if bridge_name:
        network['bridge_name'] = bridge_name

    opensand.configure('opensand', entity, network=network)

    return [opensand]


def opensand_network_ethernet(
        scenario, entity, interface, tap_name=None, bridge_name=None,
        wait_finished=None, wait_launched=None, wait_delay=0):

    opensand = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    network = {'eth': {'interface': interface}}
    if tap_name:
        network['tap_name'] = tap_name
    if bridge_name:
        network['bridge_name'] = bridge_name
    opensand.configure('opensand', entity, network=network)

    return [opensand]


def opensand_network_clear(
        scenario, entity, tap_name=None, bridge_name=None,
        wait_finished=None, wait_launched=None, wait_delay=0):

    opensand = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    network = {'clear': {}}
    if tap_name:
        network['tap_name'] = tap_name
    if bridge_name:
        network['bridge_name'] = bridge_name
    opensand.configure('opensand', entity, network=network)

    return [opensand]


def opensand_run(
        scenario, agent_entity, entity, configuration=None,
        output_address=None, logs_port=None, stats_port=None,
        binaries_directory=None, entity_id=None,
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
    opensand.configure('opensand', agent_entity, run=run)

    return [opensand]


def configure_interfaces(
        scenario, entity, interfaces, ips,
        wait_finished=None, wait_launched=None, wait_delay=0):

    for interface, ip in zip(interfaces, ips):
        wait_finished = ip_address(
                scenario, entity, interface, 'add', ip,
                wait_finished=wait_finished,
                wait_launched=wait_launched,
                wait_delay=wait_delay)
        wait_launched = None
        wait_delay = 0

    return wait_finished


def configure_routing(
        scenario, entity, network_mask, ips, gateway_ips, bridge_mac_address,
        wait_finished=None, wait_launched=None, wait_delay=0):
    wait_finished = opensand_network_ip(
            scenario, entity, network_mask,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    wait_finished = command_shell(
            scenario, entity,
            "ip link set dev opensand_tap address " + bridge_mac_address,
            wait_finished=wait_finished)

    for ip, gateway_ip in zip(ips, gateway_ips):
        wait_finished = ip_route(scenario, entity, 'add', ip, gateway_ip, wait_finished=wait_finished)

    return wait_finished


def configure_satellite(
        scenario, entity, interface, ip,
        wait_finished=None, wait_launched=None, wait_delay=0):
    return configure_interfaces(
            scenario, entity, [interface], [ip],
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)


def configure_terminal(
        scenario, entity, interfaces, ips, mask, lan_ips, gateway_ip, bridge_mac_address,
        wait_finished=None, wait_launched=None, wait_delay=0): 
    interfaces = configure_interfaces(
            scenario, entity, interfaces, ips,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    return configure_routing(
            scenario, entity, mask, lan_ips, itertools.repeat(gateway_ip), bridge_mac_address,
            wait_finished=interfaces)


def configure_gateway_phy(
        scenario, entity, interfaces, ips,
        wait_finished=None, wait_launched=None, wait_delay=0):
    return configure_interfaces(
            scenario, entity, interfaces, ips,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)


def configure_gateway(
        scenario, entity, interfaces, ips, mask, lan_ips, gateway_ips, bridge_mac_address,
        wait_finished=None, wait_launched=None, wait_delay=0):
    interfaces = configure_interfaces(
            scenario, entity, interfaces, ips,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    return configure_routing(
            scenario, entity, mask, lan_ips, gateway_ips, bridge_mac_address,
            wait_finished=interfaces)


def configure_workstation(
        scenario, entity, interface, ip, lan_ip, gateway_ip,
        wait_finished=None, wait_launched=None, wait_delay=0):
    interface = ip_address(
            scenario, entity, interface, 'add', ip,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    return ip_route(
            scenario, entity, 'add', lan_ip, gateway_ip,
            wait_finished=interface)


def clear_interfaces(
        scenario, entity, interfaces,
        wait_finished=None, wait_launched=None, wait_delay=0):

    for interface in interfaces:
        wait_finished = ip_address(
                scenario, entity, interface, 'flush',
                wait_finished=wait_finished,
                wait_launched=wait_launched,
                wait_delay=wait_delay)
        wait_launched = None
        wait_delay = 0

    return wait_finished


def clear_routing(
        scenario, entity,
        wait_finished=None, wait_launched=None, wait_delay=0):

    wait_finished = opensand_network_clear(
            scenario, entity,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    return wait_finished


def clear_satellite(
        scenario, entity, interface,
        wait_finished=None, wait_launched=None, wait_delay=0):
    return clear_interfaces(
            scenario, entity, [interface],
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)


def clear_terminal(
        scenario, entity, interfaces,
        wait_finished=None, wait_launched=None, wait_delay=0):
    interfaces = clear_interfaces(
            scenario, entity, interfaces,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    return clear_routing(
            scenario, entity,
            wait_finished=interfaces)


def clear_gateway_phy(
        scenario, entity, interfaces,
        wait_finished=None, wait_launched=None, wait_delay=0):
    return clear_interfaces(
            scenario, entity, interfaces,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)


def clear_gateway(
        scenario, entity, interfaces,
        wait_finished=None, wait_launched=None, wait_delay=0):
    interfaces = clear_interfaces(
            scenario, entity, interfaces,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    return clear_routing(
            scenario, entity,
            wait_finished=interfaces)


def clear_workstation(
        scenario, entity, interfaces, 
        wait_finished=None, wait_launched=None, wait_delay=0):
    return clear_interfaces(
            scenario, entity, [interfaces],
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
