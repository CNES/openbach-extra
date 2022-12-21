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

from scenario_builder import Scenario
from scenario_builder.helpers.network.tc_configure_link import tc_configure_link_apply
from scenario_builder.helpers.network.tc_configure_link import tc_configure_link_clear
from inspect import signature

SCENARIO_NAME = 'network_configure_link'
SCENARIO_DESCRIPTION = """This scenario allows a configuration on network interfaces
in ingress, egress or both directions in order to emulate/stop emulation of a network link like WIFI link.
Many link characteristiscs can be emulated including: bandwidth, delay, jitter and losses
"""



def tc_configure_link_scenario_apply(
        entity, ifaces, mode, bandwidth, delay_distribution,
        delay, jitter, loss_model, loss_model_params,
        buffer_size, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format('Apply'))
    tc_configure_link_apply(
            scenario, entity, ifaces, mode, bandwidth, delay_distribution,
            delay, jitter, loss_model, loss_model_params, buffer_size)
    return scenario


def tc_configure_link_scenario_clear(entity, ifaces, mode, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format('Clear'))
    tc_configure_link_clear(scenario, entity, ifaces, mode)
    return scenario


def build(entity, ifaces, mode, operation, bandwidth=None, delay=0, jitter=0,
          delay_distribution='normal', loss_model='random', loss_model_params=[0.0],
          buffer_size=10000, scenario_name=SCENARIO_NAME):
    scenario = tc_configure_link_scenario_clear(entity, ifaces, mode) if operation != 'apply' else tc_configure_link_scenario_apply (
            entity, ifaces, mode, bandwidth, delay_distribution,
            delay, jitter, loss_model, loss_model_params, buffer_size)

    if scenario_name is not None:
        scenario.name = scenario_name

    return scenario
