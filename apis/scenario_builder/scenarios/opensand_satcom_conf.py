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


from itertools import chain

from scenario_builder import Scenario
from scenario_builder.helpers.admin.push_file import push_file


SCENARIO_NAME = 'opensand_satcom_conf'
SCENARIO_DESCRIPTION = """This opensand scenario allows to:
 - Push opensand configuration files from the controller to the agents /etc/opensand folder
 - Filter the files sent depending on the type of the receiving entity
"""


def _build_remote_and_users(conf, entity_name, prefix='/etc/opensand/'):
    common_files = conf[None]
    entity_files = conf[entity_name]
    local_files = [f.as_posix() for f in chain(common_files, entity_files)]
    remote_files = [(prefix / f).as_posix() for f in common_files]
    remote_files.extend((prefix / f.relative_to(entity_name)).as_posix() for f in entity_files)
    users = ['opensand'] * len(local_files)
    groups = ['root'] * len(local_files)
    return remote_files, local_files, users, groups


def opensand_satcom_conf(satellite_entity, gw_entities, st_entities, configuration_files, scenario_name=SCENARIO_NAME):
    configuration_per_entity = {
            'sat': [],
            'st': [],
            'gw': [],
            None: [],
    }
    scenario = Scenario(scenario_name + '_files', SCENARIO_DESCRIPTION)

    for config_file in configuration_files:
        entity = config_file.parts[0]

        if entity not in configuration_per_entity:
            entity = None
        configuration_per_entity[entity].append(config_file)

    push_file(scenario, satellite_entity, *_build_remote_and_users(configuration_per_entity, 'sat'))

    files = _build_remote_and_users(configuration_per_entity, 'gw')
    for gateway in gw_entities:
        push_file(scenario, gateway, *files)

    files = _build_remote_and_users(configuration_per_entity, 'st')
    for terminal in st_entities:
        push_file(scenario, terminal, *files)

    return scenario


build = opensand_satcom_conf
