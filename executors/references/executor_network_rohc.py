#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2023 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

"""This executor builds or launches the *network_rohc* scenario from
/openbach-extra/apis/scenario_builder/scenarios/. It creates a ROHC
tunnel between 2 entities and collects compression/decompression
statistics. The tunnel can be bidirectional or unidirectional. 
It can then, optionally, plot the header compression ratio metrics using
time-series and CDF.

The platform running this scenario is supposed to have an architecture
which looks likes the following :

+-----------+                         +----------------------+     +--------------------+                         +-----------+
|  Client   |                         |         ST           |<--->|        GW          |                         |  Server   |
|           |                         |  (client_entity*)    |     |  (server_entity*)  |                         |           |
+-----------+                         +----------------------+     +--------------------+                         +-----------+
|           |                         |                      |     |                    |                         |           |
|           |<--(client_ext_ipv4/6)-->|       client_int_ipv4|<--->|server_int_ipv4     |<--(server_ext_ipv4/6)-->|           |
+-----------+                         +----------------------+     +--------------------+                         +-----------+


* 'client' and 'server' stands for the direction of the traffic (SERVER=SENDER & CLIENT=RECEIVER).
This means packets will be compressed by the server and decompressed
by the client when the user sets an unidirectional tunnel. The client-server
assotiaion does'nt matter if the tunnel is bidirectional since the 
compression/decompression will be performed by both entities.

The ROHC tunnel will be created between the 'server_entity' and the
'client_entity' based on the parameters 'server-tunnel-ipv4/6' and
'client-tunnel-ipv4/6'.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_rohc


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='Entity which compresses traffic in the ROHC tunnel.')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='Entity which decompresses traffic in the ROHC tunnel.')
    observer.add_scenario_argument(
            '--server-int-ipv4', required=True,
            help='IPv4 address of the server which communicates to the client (aka internal).')
    observer.add_scenario_argument(
            '--client-int-ipv4', required=True,
            help='IPv4 address of the client which receives traffic from the server (aka internal side).')
    observer.add_scenario_argument(
            '--server-ext-ipv4', required=True,
            help="IPv4 network address (in CIDR format) of the server's LAN (aka external side).")
    observer.add_scenario_argument(
            '--client-ext-ipv4', required=True,
            help="IPv4 network address (in CIDR format) of the client's LAN (aka external side).")
    observer.add_scenario_argument(
            '--server-ext-ipv6',
            help="IPv6 network address (in CIDR format) of the server's LAN (aka external side).") # Optional
    observer.add_scenario_argument(
            '--client-ext-ipv6',
            help="IPv6 network address (in CIDR format) of the client's LAN (aka external side).") # Optional
    observer.add_scenario_argument(
            '--server-tunnel-ipv4', default='10.10.10.1/24',
            help='IPv4 address that will be attributed to the server for the ROHC tunnel (in CIDR format).')
    observer.add_scenario_argument(
            '--client-tunnel-ipv4', default='10.10.10.2/24',
            help='IPv4 address that will be attributed to the client for the ROHC tunnel (in CIDR format).') 
    observer.add_scenario_argument(
            '--server-tunnel-ipv6', default='fd4d:4991:3faf:2::1/64',
            help='IPv6 address that will be attributed to the server for the ROHC tunnel (in CIDR format).')
    observer.add_scenario_argument(
            '--client-tunnel-ipv6', default='fd4d:4991:3faf:2::2/64',
            help='IPv6 address that will be attributed to the client for the ROHC tunnel (in CIDR format).')
    observer.add_scenario_argument(
            '--direction', choices=['unidirectional', 'bidirectional'], default='bidirectional',
            help='Choose bidirectional to compress and decompress on both server and client')
    observer.add_scenario_argument(
            '--rohc-cid-type', choices=['largecid', 'smallcid'], default='largecid',
            help='Size of CID.')
    observer.add_scenario_argument(
            '--rohc-max-contexts', type=int, default=16,
            help='Maximum number of ROHC contexts.')
    observer.add_scenario_argument(
            '--rohc-packet-size', type=int, default=1500,
            help='Maximum size of ROHC packets, not including the UDP tunnel offset.')
    observer.add_scenario_argument(
            '--duration', type=int, default=0,
            help='Duration of the ROHC tunnel application, leave blank for endless running.')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be '
            'performed (histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, network_rohc.SCENARIO_NAME)

    scenario = network_rohc.build(
            args.server_entity,
            args.client_entity,
            args.server_int_ipv4,
            args.client_int_ipv4,
            args.server_ext_ipv4,
            args.client_ext_ipv4,
            args.server_ext_ipv6,
            args.client_ext_ipv6,
            args.server_tunnel_ipv4,
            args.client_tunnel_ipv4,
            args.server_tunnel_ipv6,
            args.client_tunnel_ipv6,
            args.direction,
            args.rohc_cid_type,
            args.rohc_max_contexts,
            args.rohc_packet_size,
            args.duration,
            args.post_processing_entity,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()

