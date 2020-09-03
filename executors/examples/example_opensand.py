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

import argparse 
import ipaddress
from pathlib import Path
from itertools import chain

from auditorium_scripts.push_file import PushFile
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder import Scenario
from scenario_builder.helpers.utils import Validate, ValidateOptional, patch_print_help
from scenario_builder.helpers.access import opensand
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.scenarios import opensand_run, opensand_net_conf, opensand_satcom_conf


SCENARIO_NAME = 'Opensand'


class Entity:
    def __init__(self, entity, emulation_ip, bridge_to_lan, opensand_id, tap_name='opensand_tap', bridge_name='opensand_br', tap_mac_address=None):
        self.entity = entity
        self.opensand_id = int(opensand_id)
        self.emulation_ip = validate_ip(emulation_ip)
        self.bridge_to_lan = bridge_to_lan
        self.tap_name = tap_name
        self.bridge_name = bridge_name
        self.tap_mac_address = tap_mac_address


class GatewayPhy:
    def __init__(self, entity, net_access_entity, interco_phy, interco_net_access):
        self.entity = entity
        self.net_access_entity = net_access_entity
        self.interconnect_net_access = validate_ip(interco_net_access)
        self.interconnect_phy = validate_ip(interco_phy)


class Satellite:
    def __init__(self, entity, ip):
        self.entity = entity
        self.ip = validate_ip(ip)


class ValidateSatellite(argparse.Action):
    def __call__(self, parser, args, values, option_string=None): 
        satellite = Satellite(*values)
        setattr(args, self.dest, satellite)


class ValidateGateway(ValidateOptional, Validate):
    ENTITY_TYPE = Entity


class ValidateGatewayPhy(Validate):
    ENTITY_TYPE = GatewayPhy


class ValidateSatelliteTerminal(ValidateOptional, Validate):
    ENTITY_TYPE = Entity


def validate_ip(ip):
    return ipaddress.ip_address(ip).compressed


def example_opensand(satellite, gateways, gateways_phy, terminals, duration=0, configuration_files=None, post_processing_entity=None, scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, '')

    network_entities = [
            opensand_net_conf.OPENSAND_ENTITY(
                terrestrial.entity,
                terrestrial.tap_mac,
                terrestrial.tap_name,
                terrestrial.bridge_name,
                terrestrial.bridge_to_lan,
            )
            for terrestrial in chain(gateways, terminals)
    ]
    network_configure = scenario.add_function('start_scenario_instance')
    network_configure.configure(opensand_net_conf.build(network_entities, 'configure'))

    wait = [network_configure]
    if configuration_files:
        terminal_entities = [terminal.entity for terminal in terminals]
        gateway_entities = [gateway.entity for gateway in chain(gateways, gateways_phy)]
        push_files = scenario.add_function('start_scenario_instance', wait_finished=[network_configure])
        push_file.configure(opensand_satcom_conf.build(satellite.entity, gateway_entities, terminal_entities, configuration_files))
        wait.append(push_file)

    run_gateways = []
    for gateway in gateways:
        for gateway_phy in gateways_phy:
            if gateway.entity == gateway_phy.net_access_entity:
                run_gateways.append(opensand_run.SPLIT_GW(
                        gateway.entity,
                        gateway_phy.entity,
                        gateway.opensand_id,
                        gateway.emulation_ip,
                        gateway_phy.interconnect_net_access,
                        gateway_phy.interconnect_phy))
                break
        else:
            run_gateways.append(opensand_run.GW(
                    gateway.entity,
                    gateway.opensand_id,
                    gateway.emulation_ip))

    run = scenario.add_function('start_scenario_instance', wait_finished=wait)
    run.configure(opensand_run.build(satellite, run_gateways, terminals, duration))

    network_delete = scenario.add_function('start_scenario_instance', wait_finished=[run])
    network_delete.configure(opensand_net_conf.build(network_entities, 'delete', opensand_net_conf.SCENARIO_NAME + '_delete'))

    if post_processing_entity:
        post_processed = list(scenario.extract_function_id(opensand=opensand.opensand_find_st, include_subscenarios=True))
        if post_processed:
            time_series_on_same_graph(
                    scenario,
                    post_processing_entity,
                    post_processed,
                    [['up_return_modcod.sent_modcod']],
                    [['Sent ModCod (id)']],
                    [['UP/Return ModCod']],
                    [['Terminal {} - ModCod'.format(terminal.opensand_id) for terminal in terminals]],
                    False, [network_delete], None, 2)

        post_processed = post_processed.copy()
        post_processed.extend(scenario.extract_function_id(opensand=opensand.opensand_find_gw, include_subscenarios=True))
        post_processed.extend(scenario.extract_function_id(opensand=opensand.opensand_find_gw_phy, include_subscenarios=True))
        post_processed.extend(scenario.extract_function_id(opensand=opensand.opensand_find_gw_net_acc, include_subscenarios=True))
        if post_processed:
            legends = [
                    ['Terminal {} - Throughput from satellite'.format(st.opensand_id) for st in terminals]
                    + ['Gateway {} - Throughput from satellite'.format(gw.opensand_id) for gw in run_gateways if isinstance(gw, opensand_run.GW)]
                    + ['Gateway Phy {} - Throughput from satellite'.format(gw.opensand_id) for gw in run_gateways is isinstance(gw, opensand_run.SPLIT_GW)]
                    + ['Gateway Net Access {} - Throughput from satellite'.format(gw.opensand_id) for gw in run_gateways is isinstance(gw, opensand_run.SPLIT_GW)]
            ]
            time_series_on_same_graph(
                    scenario,
                    post_processing_entity,
                    post_processed,
                    [['throughputs.l2_from_sat.total']],
                    [['Throughput from satellite (kbps)']],
                    [['Thoughput']],
                    legends,
                    False, [network_delete], None, 2)
            cdf_on_same_graph(
                    scenario,
                    post_processing_entity,
                    post_processed_st + post_processed_gw,
                    100,
                    [['throughputs.l2_from_sat.total']],
                    [['Throughput from satellite (kbps)']],
                    [['Thoughput']],
                    legends,
                    False, [network_delete], None, 2)

    return scenario


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--sat', '-s', required=True, action=ValidateSatellite,
            nargs=2, metavar=('ENTITY', 'EMULATION_IP'),
            help='The satellite of the platform. Must be supplied only once.')
    observer.add_scenario_argument(
            '--gateway', '-gw', required=True, action=ValidateGateway, nargs='*',
            metavar='ENTITY EMULATION_IP (BRIDGE_IP | BRIDGE_INTERFACE) OPENSAND_ID [TAP_NAME [BRIDGE_NAME [TAP_MAC]]]',
            help='A gateway in the platform. Must be supplied at least once.')
    observer.add_scenario_argument(
            '--gateway-phy', '-gwp', required=False, action=ValidateGatewayPhy,
            nargs=4, metavar=('ENTITY_PHY', 'ENTITY_NET_ACC', 'INTERCONNECT_PHY', 'INTERCONNECT_NET_ACC'),
            help='The physical part of a split gateway. Must reference the '
            'net access part previously provided using the --gateway option. '
            'Optional, can be supplied only once per gateway.')
    observer.add_scenario_argument(
            '--satellite-terminal', '-st', required=True, action=ValidateSatelliteTerminal, nargs='*',
            metavar='ENTITY EMULATION_IP (BRIDGE_IP | BRIDGE_INTERFACE) OPENSAND_ID [TAP_NAME [BRIDGE_NAME [TAP_MAC]]]',
            help='A satellite terminal in the platform. Must be supplied at least once.')
    observer.add_scenario_argument(
            '--duration', '-d', required=False, default=0, type=int,
            help='Duration of the opensand run test, leave blank for endless emulation.')
    observer.add_scenario_argument(
            '--configuration-folder', '--configuration', '-c',
            required=False, type=Path, metavar='PATH',
            help='Path to a configuration folder that should be '
            'dispatched on agents before the simulation.')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')

    patch_print_help(observer.parser)
    args = observer.parse(argv, SCENARIO_NAME)

    config_files = None
    configuration_folder = args.configuration_folder
    if configuration_folder:
        config_files = [
                p.relative_to(configuration_folder)
                for extension in ('conf', 'txt', 'csv', 'input')
                for p in configuration_folder.rglob('*.' + extension)
        ]

        #Store files on the controller
        pusher = observer._share_state(PushFile)
        pusher.args.keep = True
        for config_file in config_files:
            with configuration_folder.joinpath(config_file).open() as local_file:
                pusher.args.local_file = local_file
                pusher.args.remote_path = config_file.as_posix()
                pusher.execute(False)
            # If we don't use this, the controller has a tendency to close the
            # connection after some files, so slowing things down the dirty way.
            time.sleep(0.1)

    scenario = example_opensand(
            args.sat,
            args.gateway,
            args.gateway_phy or [],
            args.satellite_terminal,
            args.duration, config_files,
            args.post_processing_entity,
            scenario_name=args.scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
