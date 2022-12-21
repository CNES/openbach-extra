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

from dataclasses import dataclass

from scenario_builder import Scenario
from scenario_builder.openbach_functions import StartJobInstance
from scenario_builder.helpers.access import opensand


SCENARIO_NAME = 'opensand_run'
SCENARIO_DESCRIPTION = """This opensand scenario allows to:
 - Run opensand in the satellite, the gateways and the STs for an opensand test
"""


@dataclass(frozen=True)
class Satellite:
    entity: str
    infrastructure: str
    topology: str


@dataclass(frozen=True)
class GroundEntity(Satellite):
    profile: str


def run(satellite, entities, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    opensand.opensand_run(scenario, satellite.entity, satellite.infrastructure, satellite.topology)

    for entity in entities:
        opensand.opensand_run(scenario, entity.entity, entity.infrastructure, entity.topology, entity.profile)

    return scenario


def build(satellite, ground_entities, duration=0, scenario_name=SCENARIO_NAME):
    scenario = run(satellite, ground_entities, scenario_name)

    if duration:
        jobs = [f for f in scenario.openbach_functions if isinstance(f, StartJobInstance)]
        scenario.add_function('stop_job_instance', wait_launched=jobs, wait_delay=duration).configure(*jobs)

    return scenario
