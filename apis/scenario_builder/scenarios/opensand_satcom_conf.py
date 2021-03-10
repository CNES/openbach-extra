#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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

import os.path
from itertools import chain
from collections import namedtuple

from scenario_builder import Scenario
from scenario_builder.helpers.admin.push_file import push_file


SCENARIO_NAME = 'opensand_satcom_conf'
SCENARIO_DESCRIPTION = """This opensand scenario allows to:
 - Push opensand configuration files from the controller to the agents /etc/opensand folder
 - Filter the files sent depending on the type of the receiving entity
"""


SAT = namedtuple('SAT', ('entity', 'infrastructure', 'topology'))
GROUND = namedtuple('GROUND', ('entity', 'infrastructure', 'topology', 'profile'))


def _configure_push_file(scenario, entity, dest_dir='/etc/opensand/'):
    entity_name = entity.entity

    files = [
            getattr(entity, name)
            for name in ('infrastructure', 'topology', 'profile')
            if hasattr(entity, name)
    ]
    local_files = [os.path.join('opensand', entity_name, f) for f in files]
    remote_files = [os.path.join(dest_dir, f) for f in files]

    push_file(
            scenario, entity_name, remote_files, local_files,
            ['root'] * len(files), ['root'] * len(files))


def opensand_satcom_conf(satellite, ground_entities, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name + '_files', SCENARIO_DESCRIPTION)

    _configure_push_file(scenario, satellite)
    for entity in ground_entities:
        _configure_push_file(scenario, entity)

    return scenario


build = opensand_satcom_conf
