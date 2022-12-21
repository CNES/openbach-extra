#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from scenario_builder.openbach_functions import StartJobInstance
from scenario_builder.helpers.service.openvpn import openvpn
from scenario_builder.helpers.service.wireguard import wireguard
from scenario_builder.helpers.network.ip_route import ip_route


SERVER_TUN_IP = "10.10.10.1"
CLIENT_TUN_IP = "10.10.10.2"
DEFAULT_CIDR = "/24"

SERVER_TUN_IP_DEFAULT = "{} if vpn is OpenVPN else {}".format(
    SERVER_TUN_IP, SERVER_TUN_IP+DEFAULT_CIDR)
CLIENT_TUN_IP_DEFAULT = "{} if vpn is OpenVPN else {}".format(
    CLIENT_TUN_IP, CLIENT_TUN_IP+DEFAULT_CIDR)

SCENARIO_NAME = 'Service VPN'
SCENARIO_DESCRIPTION = """This scenario create a VPN tunnel between a client and a server and measure throughput between.
This tunnel is created with {}.
"""


def service_vpn_scenario_wireguard(server_entity, client_entity, server_ext_ipv4, client_ext_ipv4, server_int_ipv4, client_int_ipv4, server_tun_ipv4, client_tun_ipv4,
                                 server_tun_port, client_tun_port, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format("Wireguard"))

    scenario.add_constant('server_int_ipv4', server_int_ipv4)
    scenario.add_constant('client_int_ipv4', client_int_ipv4)
    scenario.add_constant('server_ext_ipv4', server_ext_ipv4)
    scenario.add_constant('client_ext_ipv4', client_ext_ipv4)
    scenario.add_constant('server_tun_ipv4', server_tun_ipv4)
    scenario.add_constant('client_tun_ipv4', client_tun_ipv4)
    scenario.add_constant('server_tun_port', server_tun_port)
    scenario.add_constant('client_tun_port', client_tun_port)

    wireguard(scenario, server_entity, client_entity, '$server_int_ipv4', client_ip='$client_int_ipv4', server_listen_port='$server_tun_port', client_listen_port='$client_tun_port',
              server_tun_ip='$server_tun_ipv4', client_tun_ip='$client_tun_ipv4')

    jobs = [f for f in scenario.openbach_functions if isinstance(f, StartJobInstance)]
    server_route_v4 = ip_route(scenario, server_entity, 'replace', '$client_ext_ipv4', device='tun0', restore=True,
        wait_launched=jobs, wait_delay=5)
    client_route_v4 = ip_route(scenario, client_entity, 'replace', '$server_ext_ipv4', device='tun0', restore=True,
        wait_launched=jobs, wait_delay=5)

    return scenario


def service_vpn_scenario_openvpn(server_entity, client_entity, server_ext_ipv4, client_ext_ipv4, server_int_ipv4, client_int_ipv4, server_tun_ipv4, client_tun_ipv4,
                                 server_tun_port, client_tun_port, opvpn_protocol, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format("OpenVPN "+opvpn_protocol.upper()))

    scenario.add_constant('server_int_ipv4', server_int_ipv4)
    scenario.add_constant('client_int_ipv4', client_int_ipv4)
    scenario.add_constant('server_ext_ipv4', server_ext_ipv4)
    scenario.add_constant('client_ext_ipv4', client_ext_ipv4)
    scenario.add_constant('server_tun_ipv4', server_tun_ipv4)
    scenario.add_constant('client_tun_ipv4', client_tun_ipv4)
    scenario.add_constant('server_tun_port', server_tun_port)
    scenario.add_constant('client_tun_port', client_tun_port)
    scenario.add_constant('opvpn_protocol', opvpn_protocol)

    openvpn(scenario, server_entity, '$server_int_ipv4',
            client_entity, client_ip='$client_int_ipv4', protocol='$opvpn_protocol', server_port='$server_tun_port', client_port='$client_tun_port',
            server_tun_ip='$server_tun_ipv4', client_tun_ip='$client_tun_ipv4')

    jobs = [f for f in scenario.openbach_functions if isinstance(f, StartJobInstance)]
    server_route_v4 = ip_route(scenario, server_entity, 'replace', '$client_ext_ipv4', device='tun0', restore=True,
        wait_launched=jobs, wait_delay=5)
    client_route_v4 = ip_route(scenario, client_entity, 'replace', '$server_ext_ipv4', device='tun0', restore=True,
        wait_launched=jobs, wait_delay=5)

    return scenario


def build(server_entity, client_entity, server_ext_ipv4, client_ext_ipv4, server_int_ipv4, client_int_ipv4, server_tun_ipv4, client_tun_ipv4,
          server_tun_port, client_tun_port, vpn, opvpn_protocol, duration=0, scenario_name=SCENARIO_NAME):

    scenario = None

    if vpn == "openvpn":
        if server_tun_ipv4 == SERVER_TUN_IP_DEFAULT:
            server_tun_ipv4 = SERVER_TUN_IP
        if client_tun_ipv4 == CLIENT_TUN_IP_DEFAULT:
            client_tun_ipv4 = CLIENT_TUN_IP
        scenario = service_vpn_scenario_openvpn(
            server_entity, client_entity, server_ext_ipv4, client_ext_ipv4, server_int_ipv4, client_int_ipv4,
            server_tun_ipv4, client_tun_ipv4, server_tun_port, client_tun_port, opvpn_protocol, scenario_name=scenario_name)
    else:
        if server_tun_ipv4 == SERVER_TUN_IP_DEFAULT:
            server_tun_ipv4 = SERVER_TUN_IP+DEFAULT_CIDR
        if client_tun_ipv4 == CLIENT_TUN_IP_DEFAULT:
            client_tun_ipv4 = CLIENT_TUN_IP+DEFAULT_CIDR
        scenario = service_vpn_scenario_wireguard(
            server_entity, client_entity, server_ext_ipv4, client_ext_ipv4, server_int_ipv4, client_int_ipv4,
            server_tun_ipv4, client_tun_ipv4, server_tun_port, client_tun_port, scenario_name=scenario_name)

    if duration:
        jobs = [f for f in scenario.openbach_functions if isinstance(f, StartJobInstance)]
        scenario.add_function('stop_job_instance', wait_launched=jobs, wait_delay=duration).configure(*jobs)

    return scenario
