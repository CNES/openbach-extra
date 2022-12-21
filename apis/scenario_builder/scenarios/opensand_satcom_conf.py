#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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

from pathlib import Path
from dataclasses import dataclass

from scenario_builder import Scenario
from scenario_builder.helpers.admin.push_file import push_file


SCENARIO_NAME = 'opensand_satcom_conf'
SCENARIO_DESCRIPTION = """This opensand scenario allows to:
 - Push opensand configuration files from the controller to the agents /etc/opensand folder
 - Filter the files sent depending on the type of the receiving entity
"""


@dataclass(frozen=True)
class OpensandEntity:
    entity: str
    infrastructure: Path = None
    topology: Path = None
    profile: Path = None


def _configure_push_file(scenario, entity, dest_dir=Path('/etc/opensand/')):
    files = [
            filepath
            for name in ('infrastructure', 'topology', 'profile')
            if (filepath := getattr(entity, name, None)) is not None
    ]
    local_files = [f.as_posix() for f in files]
    remote_files = [dest_dir.joinpath(f.name).as_posix() for f in files]

    if files_length := len(files):
        push_file(
                scenario, entity.entity, remote_files, local_files,
                ['root'] * files_length, ['root'] * files_length)


def opensand_satcom_conf(opensand_entities, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name + '_files', SCENARIO_DESCRIPTION)

    for entity in opensand_entities:
        _configure_push_file(scenario, entity)

    return scenario


build = opensand_satcom_conf
