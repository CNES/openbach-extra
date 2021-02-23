#!/usr/bin/env python

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

"""TCP Evaluation Suite

This scenario provides a scenario that enables the evaluation of TCP
congestion controls.

The architecture should be the following

   +--------------+                                +--------------+
   | endpointA    |                                | endpointC    |
   +--------------+----+                  +--------+--------------+
                       |                  |
                     +-+-------+     +---------+
                     |Router L |     |Router R |
                     +-+-------+-----+-------+-+
                       |                     |
   +--------------+----+                     +-----+--------------+
   | endpointB    |                                | endpointD    |
   +--------------+                                +--------------+

Here are the values that should be specified by default but available for
parametrisation by the user.

+-------------------------------------+
endpointA and endpointC parameters:
  - Congestion control : CUBIC
  - IW : 10
endpointB and endpointD parameters:
  - Congestion control : CUBIC
  - IW : 10
endpointA <-> Router L,
endpointB <-> Router L,
Router R <-> endpointC,
Router R <-> endpointD,
  - bandwidth : 100 Mbps
  - latency : 10 ms
  - loss : 0%
Router L <-> Router R:
  - bandwidth : 20 Mbps
  - latency : 10 ms
  - loss : 0%
    at t=0+10s
  - bandwidth : 10 Mbps
  - latency : 10 ms
  - loss : 0%
    at t=10+10s
  - bandwidth : 20 Mbps
  - latency : 10 ms
  - loss : 0%
+-------------------------------------+

+-------------------------------------+
Traffic:
  - direction_A-C : forward or return
    (default forward)
  - direction_B-D : forward or return
    (default forward)
  - flow_size_B-D :
    - start at tBD=0
    - 500 MB
    - n_flow = 1 (can be 0)
  - flow_size_A-C :
    - start at tAC=tBD+5 sec
    - 10 MB
    - n_flow : 1
    - repeat : 10
+-------------------------------------+

+-------------------------------------+
Metrics:
  - CWND for all the flows as function of time
  - Received throughput at the receiver for all entities receiving data as a function of time
  - Time needed to transmit flow_A-C (CDF)
  - bandwidth L <-> R usage (%) as function of time
+-------------------------------------+

"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import tcp_evaluation_suite

def main(argv=None):

    observer = ScenarioObserver()

    observer.add_scenario_argument(
            '--endpointA', required=True,
            help='')
    observer.add_scenario_argument(
            '--endpointB', required=True,
            help='')
    observer.add_scenario_argument(
            '--endpointC', required=True,
            help='')
    observer.add_scenario_argument(
            '--endpointD', required=True,
            help='')
    observer.add_scenario_argument(
            '--routerL', required=True,
            help='')
    observer.add_scenario_argument(
            '--routerR', required=True,
            help='')
    observer.add_scenario_argument(
            '--endpointA_network_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--endpointB_network_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--endpointC_network_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--endpointD_network_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--routerL_to_endpointA_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--routerL_to_endpointB_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--routerR_to_endpointC_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--routerR_to_endpointD_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--routerL_to_routerR_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--routerR_to_routerL_ip', required=True,
            help='')
    observer.add_scenario_argument(
            '--interface_AL', required=True,
            help='')
    observer.add_scenario_argument(
            '--interface_BL', required=True,
            help='')
    observer.add_scenario_argument(
            '--interface_CR', required=True,
            help='')
    observer.add_scenario_argument(
            '--interface_DR', required=True,
            help='')
    observer.add_scenario_argument(
            '--interface_RA', required=True,
            help='')
    observer.add_scenario_argument(
            '--interface_RB', required=True,
            help='')
    observer.add_scenario_argument(
            '--interface_LC', required=True,
            help='')
    observer.add_scenario_argument(
            '--interface_LD', required=True,
            help='')

    observer.add_scenario_argument(
            '--congestion-control', required=True,
            help='Congestion control name')

    args = observer.parse(argv, tcp_evaluation_suite.SCENARIO_NAME)

    scenario = tcp_evaluation_suite.build(
            args.endpointA,
            args.endpointB,
            args.endpointC,
            args.endpointD,
            args.routerL,
            args.routerR,
            args.endpointA_network_ip,
            args.endpointB_network_ip,
            args.endpointC_network_ip,
            args.endpointD_network_ip,
            args.routerL_to_endpointA_ip,
            args.routerL_to_endpointB_ip,
            args.routerR_to_endpointC_ip,
            args.routerR_to_endpointD_ip,
            args.routerL_to_routerR_ip,
            args.routerR_to_routerL_ip,
            args.interface_AL,
            args.interface_BL,
            args.interface_CR,
            args.interface_DR,
            args.interface_RA,
            args.interface_RB,
            args.interface_LC,
            args.interface_LD,
            congestion_control=args.congestion_control,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
