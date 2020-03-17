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

import itertools
from collections import namedtuple

from scenario_builder import Scenario
from scenario_builder.helpers.access import opensand
from scenario_builder.helpers.admin.push_file import push_file


SCENARIO_DESCRIPTION = """This run opensand scenario allows to:
 - Run opensand in the satellite, the gateways and the STs for an opensand test
"""
SCENARIO_NAME = 'access_opensand_run'

PUSH_DESCRIPTION = """This push file scenario allows to:
 - Push conf files to the satellite, the gateways, and the ST from the controller
"""
PUSH_NAME = 'access_opensand_push'


SAT = namedtuple('SAT', ('entity', 'ip'))
ST = namedtuple('ST', ('entity', 'opensand_id', 'emulation_ip'))
GW = namedtuple('GW', ('entity', 'opensand_id', 'emulation_ip'))
SPLIT_GW = namedtuple('SPLIT_GW', (
    'entity_net_acc', 'entity_phy', 'opensand_id', 'emulation_ip',
    'interconnect_ip_net_acc', 'interconnect_ip_phy'))


def run(satellite, gateways, terminals, scenario_name=SCENARIO_NAME):
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
            continue  # TODO:~fail ?

    for terminal in terminals:
        opensand.opensand_run(
                scenario, terminal.entity, 'st',
                entity_id=terminal.opensand_id,
                emulation_address=terminal.emulation_ip)

    return scenario


def _build_remote_and_users(configuration_per_entity, entity_name, prefix='/etc/opensand/'):
    common_files = configuration_per_entity[None]
    entity_files = configuration_per_entity[entity_name]
    local_files = [f.as_posix() for f in itertools.chain(common_files, entity_files)]
    remote_files = [(prefix / f).as_posix() for f in common_files]
    remote_files.extend((prefix / f.relative_to(entity_name)).as_posix() for f in entity_files)
    users = ['opensand'] * len(local_files)
    groups = ['root'] * len(local_files)
    return remote_files, local_files, users, groups


def push_conf(satellite_entity, gateways, terminals, configuration_files, scenario_name=PUSH_NAME):
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

    scenario = Scenario(scenario_name, PUSH_DESCRIPTION)

    push_file(scenario, satellite_entity, *_build_remote_and_users(configuration_per_entity, 'sat'))
    for gateway in gateways:
        files = _build_remote_and_users(configuration_per_entity, 'gw')
        if isinstance(gateway, GW):
            push_file(scenario, gateway.entity, *files)
        elif isinstance(gateway, SPLIT_GW):
            push_file(scenario, gateway.entity_net_acc, *files)
            push_file(scenario, gateway.entity_phy, *files)
        else:
            continue  # TODO:~fail ?

    files = _build_remote_and_users(configuration_per_entity, 'st')
    for terminal in terminals:
        push_file(scenario, terminal.entity, *files)

    return scenario


def build(satellite, gateways, terminals, duration=0, configuration_files=None, scenario_name=SCENARIO_NAME):
    scenario = None
    scenario_run = run(satellite, gateways, terminals, scenario_name)

    if configuration_files:
        scenario_push = push_conf(satellite.entity, gateways, terminals, configuration_files)

        scenario = Scenario(scenario_name + '_with_configuration_files')
        start_scenario = scenario.add_function('start_scenario_instance')
        start_scenario.configure(scenario_push)

        start_scenario = scenario.add_function('start_scenario_instance', wait_finished=[start_scenario])
        start_scenario.configure(scenario_run)

    if duration:
        if scenario is None:
            scenario = Scenario(scenario_name + '_limited_time')
            start_scenario = scenario.add_function('start_scenario_instance')
            start_scenario.configure(scenario_run)

        scenario.add_function('stop_scenario_instance', wait_launched=[start_scenario], wait_delay=duration).configure(start_scenario)

    return scenario_run if scenario is None else scenario
