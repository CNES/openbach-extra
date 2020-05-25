#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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

import ipaddress
from collections import namedtuple

from scenario_builder import Scenario
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance
from scenario_builder.helpers.access import opensand
from scenario_builder.helpers.admin.push_file import push_file


SCENARIO_NAME = 'access_opensand'
SCENARIO_DESCRIPTION = """This opensand scenario allows to:
 - Configure bridge/tap interfaces on entities for OpenSAND to communicate with the real world
 - Optionnaly send configuration files on entities
 - Run opensand in the satellite, the gateways and the STs for an opensand test
"""


SAT = namedtuple('SAT', ('entity', 'ip'))
ST = namedtuple('ST', ('entity', 'opensand_id', 'tap_mac', 'tap_name', 'bridge_name', 'bridge_to_lan', 'emulation_ip'))
GW = namedtuple('GW', ('entity', 'opensand_id', 'tap_mac', 'tap_name', 'bridge_name', 'bridge_to_lan', 'emulation_ip'))
SPLIT_GW = namedtuple('SPLIT_GW', (
    'entity_net_acc', 'entity_phy', 'opensand_id', 'tap_mac', 'tap_name', 'bridge_name',
    'bridge_to_lan', 'emulation_ip', 'interconnect_ip_net_acc', 'interconnect_ip_phy'))


def _opensand_network_implementation(bridge_to_lan_interface):
    try:
        ipaddress.ip_interface(bridge_to_lan_interface)
    except ValueError:
        return opensand.opensand_network_ethernet
    else:
        return opensand.opensand_network_ip


def run(satellite, gateways, terminals, scenario_name=SCENARIO_NAME + '_run'):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    opensand.opensand_run(scenario, satellite.entity, 'sat', emulation_address=satellite.ip)

    for gateway in gateways:
        if isinstance(gateway, GW):
            opensand.opensand_run(
                    scenario, gateway.entity, 'gw',
                    entity_id=gateway.opensand_id,
                    emulation_address=gateway.emulation_ip)
        elif isinstance(gateway, SPLIT_GW):
            opensand.opensand_run(
                    scenario, gateway.entity_net_acc, 'gw-net-acc',
                    entity_id=gateway.opensand_id,
                    interconnection_address=gateway.interconnect_ip_net_acc)
            opensand.opensand_run(
                    scenario, gateway.entity_phy, 'gw-phy',
                    entity_id=gateway.opensand_id,
                    emulation_address=gateway.emulation_ip,
                    interconnection_address=gateway.interconnect_ip_phy)
        else:
            continue  # TODO: fail?

    for terminal in terminals:
        opensand.opensand_run(
                scenario, terminal.entity, 'st',
                entity_id=terminal.opensand_id,
                emulation_address=terminal.emulation_ip)

    return scenario


def access_opensand(satellite, gateways, terminals, configuration_files=None, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    wait = []
    for gateway in gateways:
        if isinstance(gateway, GW):
            entity = gateway.entity
        elif isinstance(gateway, SPLIT_GW):
            entity = gateway.entity_net_acc
        else:
            continue  # TODO: fail?
        wait += _opensand_network_implementation(gateway.bridge_to_lan)(
                scenario, entity, gateway.bridge_to_lan,
                gateway.tap_name, gateway.bridge_name, gateway.tap_mac)

    for terminal in terminals:
        wait += _opensand_network_implementation(terminal.bridge_to_lan)(
                scenario, terminal.entity, terminal.bridge_to_lan,
                terminal.tap_name, terminal.bridge_name, terminal.tap_mac)

    if configuration_files:
        configuration_per_entity = {
                'sat': [],
                'st': [],
                'gw': [],
                None: [],
        }

        for config_file in configuration_files:
            entity = config_file.parts[0]

            if entity not in configuration_per_entity:
                entity = None
            configuration_per_entity[entity].append(config_file)

        def _build_remote_and_users(entity_name, prefix='/etc/opensand/'):
            common_files = configuration_per_entity[None]
            entity_files = configuration_per_entity[entity_name]
            local_files = [f.as_posix() for f in itertools.chain(common_files, entity_files)]
            remote_files = [(prefix / f).as_posix() for f in common_files]
            remote_files.extend((prefix / f.relative_to(entity_name)).as_posix() for f in entity_files)
            users = ['opensand'] * len(local_files)
            groups = ['root'] * len(local_files)
            return remote_files, local_files, users, groups

        wait += push_file(scenario, satellite.entity, *_build_remote_and_users('sat'))

        files = _build_remote_and_users('gw')
        for gateway in gateways:
            if isinstance(gateway, GW):
                wait += push_file(scenario, gateway.entity, *files)
            elif isinstance(gateway, SPLIT_GW):
                wait += push_file(scenario, gateway.entity_net_acc, *files)
                wait += push_file(scenario, gateway.entity_phy, *files)

        files = _build_remote_and_users('st')
        for terminal in terminals:
            wait += push_file(scenario, terminal.entity, *files)

    opensand_run = scenario.add_function('start_scenario_instance', wait_finished=wait)
    opensand_run.configure(run(satellite, gateways, terminals, scenario_name + '_run'))

    for gateway in gateways:
        if isinstance(gateway, GW):
            entity = gateway.entity
        elif isinstance(gateway, SPLIT_GW):
            entity = gateway.entity_net_acc
        else:
            continue
        opensand.opensand_network_clear(
                scenario, entity, gateway.tap_name,
                gateway.bridge_name, wait_finished=[opensand_run])

    for terminal in terminals:
        opensand.opensand_network_clear(
                scenario, terminal.entity, terminal.tap_name,
                terminal.bridge_name, wait_finished=[opensand_run])

    return scenario


def build(satellite, gateways, terminals, duration=0, configuration_files=None, scenario_name=SCENARIO_NAME):
    scenario = access_opensand(satellite, gateways, terminals, configuration_files, scenario_name)

    if duration:
        scenario_run, = (s for s in scenario.openbach_functions if isinstance(s, StartScenarioInstance))
        jobs = [f for f in scenario_run.openbach_functions if isinstance(f, StartJobInstance)]
        scenario_run.add_function('stop_job_instance', wait_launched=jobs, wait_delay=duration).configure(*jobs)

    return scenario
