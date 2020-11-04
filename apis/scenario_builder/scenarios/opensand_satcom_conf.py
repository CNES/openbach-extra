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


def _configure_push_file(scenario, entity_name, entity_type, conf, files, dest_dir='/etc/opensand/'):
    try:
        entity_files = files[entity_name]
    except KeyError:
        common_files = conf[None]
        entity_files = conf[entity_type]
        local_files = [('opensand' / f).as_posix() for f in chain(common_files, entity_files)]
        remote_files = [(prefix / f).as_posix() for f in common_files]
        remote_files.extend((prefix / f.relative_to(entity_name)).as_posix() for f in entity_files)
    else:
        storage_folder = 'opensand_' + entity_name
        local_files = [(storage_folder / f).as_posix() for f in entity_files]
        remote_files = [(dest_dir / f).as_posix() for f in entity_files]

    files_count = len(local_files)
    assert len(remote_files) == files_count

    if files_count:
        push_file(
                scenario, entity_name, remote_files, local_files,
                ['opensand'] * files_count, ['root'] * files_count)


def opensand_satcom_conf(satellite_entity, gw_entities, st_entities, configuration_files, scenario_name=SCENARIO_NAME):
    configuration_per_entity = {
            'sat': [],
            'st': [],
            'gw': [],
            None: [],
    }
    scenario = Scenario(scenario_name + '_files', SCENARIO_DESCRIPTION)

    for config_file in configuration_files.get(None, []):
        entity = config_file.parts[0]

        if entity not in configuration_per_entity:
            entity = None
        configuration_per_entity[entity].append(config_file)

    _configure_push_file(scenario, satellite_entity, 'sat', configuration_per_entity, configuration_files)
    for gateway in gw_entities:
        _configure_push_file(scenario, gateway, 'gw', configuration_per_entity, configuration_files)
    for terminal in st_entities:
        _configure_push_file(scenario, terminal, 'st', configuration_per_entity, configuration_files)

    return scenario


build = opensand_satcom_conf
