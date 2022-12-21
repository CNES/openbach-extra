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

import warnings
import ipaddress
from dataclasses import dataclass
from typing import Optional, Union

from scenario_builder import Scenario
from scenario_builder.helpers.network.ip_route import ip_route
from scenario_builder.helpers.network.ip_tuntap import ip_tuntap
from scenario_builder.helpers.network.ip_address import ip_address
from scenario_builder.helpers.transport.sysctl import sysctl_configure_ip_forwarding
from scenario_builder.helpers.network.ip_link import ip_link_add, ip_link_set, ip_link_del


SCENARIO_NAME = 'opensand_net_conf'
SCENARIO_DESCRIPTION = """This opensand scenario allows to:
 - Configure bridge/tap interfaces on entities for OpenSAND to communicate with the real world
 - Configure ip forwarding in case IP mode is requested
 - Clear the configuration if requested
"""


@dataclass(frozen=True)
class OpensandEntity:
    name: str
    tap_mac: Optional[str]
    tap_name: str
    bridge_name: str
    bridge_to_lan: Union[ipaddress._BaseAddress,str,None]


def opensand_network_ip(
        scenario, entity, address_mask, tap_name='opensand_tap',
        bridge_name='opensand_br', tap_mac_address=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    tap_add = ip_tuntap(
            scenario, entity, tap_name, 'add',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    bridge_add = ip_link_add(
            scenario, entity, bridge_name, type='bridge',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    if tap_mac_address is not None:
        tap_add = ip_link_set(scenario, entity, tap_name, address=tap_mac_address, wait_finished=tap_add)

    bridge_add = ip_address(scenario, entity, bridge_name, 'add', address_mask, wait_finished=bridge_add)
    tap_in_bridge = ip_link_set(scenario, entity, tap_name, master=bridge_name, wait_finished=tap_add + bridge_add)

    tap_up = ip_link_set(scenario, entity, tap_name, state='up', wait_finished=tap_in_bridge)
    bridge_up = ip_link_set(scenario, entity, bridge_name, state='up', wait_finished=tap_in_bridge)

    try:
        interface = ipaddress.ip_interface(address_mask)
    except ValueError:
        # Do not bother much as `ip_address` will likely fail anyway
        return tap_up + bridge_up
    else:
        return sysctl_configure_ip_forwarding(
                scenario, entity, bridge_name,
                version=interface.version,
                wait_finished=tap_up + bridge_up)


def opensand_network_ethernet(
        scenario, entity, interface, tap_name='opensand_tap',
        bridge_name='opensand_br', tap_mac_address=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    tap_add = ip_tuntap(
            scenario, entity, tap_name, 'add',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    bridge_add = ip_link_add(
            scenario, entity, bridge_name, type='bridge',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    if tap_mac_address is not None:
        tap_add = ip_link_set(scenario, entity, tap_name, address=tap_mac_address, wait_finished=tap_add)

    tap_in_bridge = ip_link_set(scenario, entity, tap_name, master=bridge_name, wait_finished=tap_add + bridge_add)
    interface_in_bridge = ip_link_set(scenario, entity, interface, master=bridge_name, wait_finished=bridge_add)

    wait = tap_in_bridge + interface_in_bridge
    tap_up = ip_link_set(scenario, entity, tap_name, state='up', wait_finished=wait)
    bridge_up = ip_link_set(scenario, entity, bridge_name, state='up', wait_finished=wait)

    return tap_up + bridge_up


def opensand_network_clear(
        scenario, entity, tap_name, bridge_name,
        wait_finished=None, wait_launched=None, wait_delay=0):
    tap_del = ip_link_del(
            scenario, entity, tap_name,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    bridge_del = ip_link_del(
            scenario, entity, bridge_name,
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    return tap_del + bridge_del


def opensand_net_conf_apply(entities, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    for entity in entities:
        try:
            address_mask = ipaddress.ip_interface(entity.bridge_to_lan)
        except ValueError:
            network_configure = opensand_network_ethernet
            bridge = entity.bridge_to_lan
        else:
            network_configure = opensand_network_ip
            if address_mask.network.prefixlen == address_mask.max_prefixlen:
                warnings.warn('Bridge IP specified without a netmask or referencing a single address; this may not be what you want.')
            bridge = address_mask.with_prefixlen
        network_configure(
                scenario, entity.name, bridge,
                entity.tap_name, entity.bridge_name, entity.tap_mac)

    return scenario


def opensand_net_conf_delete(entities, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    for entity in entities:
        opensand_network_clear(scenario, entity.name, entity.tap_name, entity.bridge_name)

    return scenario


def build(entities, mode='configure', scenario_name=SCENARIO_NAME):
    if mode == 'configure':
        return opensand_net_conf_apply(entities, scenario_name)
    elif mode == 'delete':
        return opensand_net_conf_delete(entities, scenario_name)
    else:
        raise ValueError('mode should be either \'configure\' or \'delete\'')
