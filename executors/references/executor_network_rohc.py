#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2020 CNES
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

+-----------+                           +----------------------+      +--------------------+                         +-----------+
|  Client   |                           |         ST           |<---->|        GW          |                         |  Server   |
|           |                           |  (receiver_entity*)  |      |  (sender_entity*)  |                         |           |
+-----------+                           +----------------------+      +--------------------+                         +-----------+
|           |                           |                      |      |                    |                         |           |
|           |<--(receiver_lan_ipv4/6)-->|     receiver_sat_ipv4|<---->|sender_sat_ipv4     |<--(sender_lan_ipv4/6)-->|           |
+-----------+                           +----------------------+      +--------------------+                         +-----------+


* 'receiver' and 'sender' stands for the direction of the traffic.
That means that packets will be compressed by the sender and decompressed
by the receiver when the user sets an unidirectional tunnel. The receiver-sender
assotiaion does'nt matter if the tunnel is bidirectional since the 
compression/decompression will be performed by both entities.

The ROHC tunnel will be created between the 'sender_entity' and the
'receiver_entity' based on the parameters 'sender-tunnel-ipv4/6' and
'receiver-tunnel-ipv4/6'.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_rohc


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--sender-entity', required=True,
            help='Entity which compresses traffic in the ROHC tunnel.')
    observer.add_scenario_argument(
            '--receiver-entity', required=True,
            help='Entity which decompresses traffic in the ROHC tunnel.')
    observer.add_scenario_argument(
            '--sender-sat-ipv4', required=True,
            help='IPv4 address of the sender which communicates to the receiver (aka satellite side).')
    observer.add_scenario_argument(
            '--receiver-sat-ipv4', required=True,
            help='IPv4 address of the receiver which receives traffic from the sender (aka satellite side).')
    observer.add_scenario_argument(
            '--sender-lan-ipv4', required=True,
            help="IPv4 network address of the sender's LAN (in CIDR format).")
    observer.add_scenario_argument(
            '--receiver-lan-ipv4', required=True,
            help="IPv4 network address of the receiver's LAN (in CIDR format).")
    observer.add_scenario_argument(
            '--sender-lan-ipv6',
            help="IPv6 network address of the sender's LAN (in CIDR format).") # Optional
    observer.add_scenario_argument(
            '--receiver-lan-ipv6',
            help="IPv6 network address of the receiver's LAN (in CIDR format).") # Optional
    observer.add_scenario_argument(
            '--sender-tunnel-ipv4', default='10.10.10.1/24',
            help='IPv4 address that will be attributed to the sender for the ROHC tunnel (in CIDR format).')
    observer.add_scenario_argument(
            '--receiver-tunnel-ipv4', default='10.10.10.2/24',
            help='IPv4 address that will be attributed to the receiver for the ROHC tunnel (in CIDR format).') 
    observer.add_scenario_argument(
            '--sender-tunnel-ipv6', default='fd4d:4991:3faf:2::1/64',
            help='IPv6 address that will be attributed to the sender for the ROHC tunnel (in CIDR format).')
    observer.add_scenario_argument(
            '--receiver-tunnel-ipv6', default='fd4d:4991:3faf:2::2/64',
            help='IPv6 address that will be attributed to the receiver for the ROHC tunnel (in CIDR format).')
    observer.add_scenario_argument(
            '--direction', choices=['unidirectional', 'bidirectional'], default='bidirectional',
            help='Choose bidirectional to compress and decompress on both sender and receiver')
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
            args.sender_entity,
            args.receiver_entity,
            args.sender_sat_ipv4,
            args.receiver_sat_ipv4,
            args.sender_lan_ipv4,
            args.receiver_lan_ipv4,
            args.sender_lan_ipv6,
            args.receiver_lan_ipv6,
            args.sender_tunnel_ipv4,
            args.receiver_tunnel_ipv4,
            args.sender_tunnel_ipv6,
            args.receiver_tunnel_ipv6,
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

