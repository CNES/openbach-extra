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

"""This executor builds and launches the *transport_tcp_stack_conf* scenario
from /openbach-extra/apis/scenario_builder/scenarios/

If reset option is set, the sysctl and CUBIC parameters are reset to the value
they had at the installation of the job of tcp_conf_linux. Then the parameters
are updated only if a new value is set in the arguments. More information on
the wiki page of the job tcp_conf_linux :
https://github.com/CNES/openbach-extra/tree/master/externals_jobs/stable_jobs/transport/tcp_conf_linux

The job ip_route needs the following arguments to run:
- dest_ip
- operation
- gw_ip or dev
If no argument neither icwnd and irwnd are set, the job is not launched. If at
least one argument is set but not all for the above list, this script stops.
"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import transport_tcp_stack_conf
from scenario_builder.helpers.utils import filter_none


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', required=True,
            help='Name of the openabch entity to apply configuration on')

    observer.add_scenario_argument(
            '--reset', action='store_true',
            help='Reset the parameters to default configuration before applying changes')
    observer.add_scenario_argument(
            '--tcp_slow_start_after_idle', type=int, choices=[0, 1],
            help='The tcp_slow_start_after_idle field')
    observer.add_scenario_argument(
            '--tcp_no_metrics_save', type=int, choices=[0, 1],
            help='The tcp_no_metrics_save field')
    observer.add_scenario_argument(
            '--tcp_sack', type=int, choices=[0, 1],
            help='The tcp_sack field')
    observer.add_scenario_argument(
            '--tcp_recovery', type=int, choices=[1, 2, 4],
            help='The tcp_recovery field')
    observer.add_scenario_argument(
            '--tcp_wmem_min', type=int,
            help='The tcp_wmem_min field')
    observer.add_scenario_argument(
            '--tcp_wmem_default', type=int,
            help='The tcp_wmem_default field')
    observer.add_scenario_argument(
            '--tcp_wmem_max', type=int,
            help='The tcp_wmem_max field')
    observer.add_scenario_argument(
            '--tcp_rmem_min', type=int,
            help='The tcp_rmem_min field')
    observer.add_scenario_argument(
            '--tcp_rmem_default', type=int,
            help='The tcp_rmem_default field')
    observer.add_scenario_argument(
            '--tcp_rmem_max', type=int,
            help='The tcp_rmem_max field')
    observer.add_scenario_argument(
            '--tcp_fastopen', type=int, choices=[1, 2, 4, 200, 400],
            help='The tcp_fastopen field')
    observer.add_scenario_argument(
            '--core_wmem_default', type=int,
            help='The core_wmem_default field')
    observer.add_scenario_argument(
            '--core_wmem_max', type=int,
            help='The core_wmem_max field')
    observer.add_scenario_argument(
            '--core_rmem_default', type=int,
            help='The core_rmem_default field')
    observer.add_scenario_argument(
            '--core_rmem_max', type=int,
            help='The core_rmem_max field')

    observer.add_scenario_argument(
            '--congestion-control', required=True,
            help='Congestion control name')

    observer.add_scenario_argument(
            '--beta', type=int,
            help='The beta field of CUBIC (only used when congestion_control is CUBIC')
    observer.add_scenario_argument(
            '--fast_convergence', type=int,
            help='The fast_convergence field of CUBIC (only used when congestion_control is CUBIC')
    observer.add_scenario_argument(
            '--hystart_ack_delta', type=int,
            help='The hystart_ack_delta field of CUBIC (only used when congestion_control is CUBIC')
    observer.add_scenario_argument(
            '--hystart_low_window', type=int,
            help='The hystart_low_window field of CUBIC (only used when congestion_control is CUBIC')
    observer.add_scenario_argument(
            '--tcp_friendliness', type=int,
            help='The tcp_friendliness field of CUBIC (only used when congestion_control is CUBIC')
    observer.add_scenario_argument(
            '--hystart', type=int,
            help='The hystart field of CUBIC (only used when congestion_control is CUBIC')
    observer.add_scenario_argument(
            '--hystart_detect', type=int,
            help='The hystart_detect field of CUBIC (only used when congestion_control is CUBIC')
    observer.add_scenario_argument(
            '--initial_ssthresh', type=int,
            help='The initial_ssthresh field of CUBIC (only used when congestion_control is CUBIC')

    observer.add_scenario_argument(
            '--interface', '--network-interface',
            help='Interface to configure segementation offload on')
    observer.add_scenario_argument(
            '--dest-ip', '--destination-ip',
            help='Ip address of the destination network')
    observer.add_scenario_argument(
            '--operation', choices=["add", "change", "delete"],
            help='Select the operation to apply')
    observer.add_scenario_argument(
            '--gw-ip', '--gateway-ip',
            help='Ip address of the gateway')
    observer.add_scenario_argument(
            '--dev', '--device',
            help='Output device name')
    observer.add_scenario_argument(
            '--icwnd', '--initcwnd',
            help='Initial congestion window size for connections to specified destination')
    observer.add_scenario_argument(
            '--irwnd', '--initrwnd',
            help='Initial receive window size for connections to specified destination')

    args = observer.parse(argv, transport_tcp_stack_conf.SCENARIO_NAME)

    route = filter_none(
            destination_ip=args.dest_ip,
            gateway_ip=args.gw_ip,
            operation=args.operation,
            device=args.dev,
            initcwnd=args.icwnd,
            initrwnd=args.irwnd)

    if route and (args.dest_ip is None or args.operation is None or (args.gw_ip is None and args.dev is None)):
            observer.parser.error("""
WARNING: The following arguments are mandatory when setting the iproute rules or setting icwnd and rcwnd:
 - dest_ip
 - operation
 - gw_ip or dev""")

    scenario = transport_tcp_stack_conf.build(
            args.entity, args.congestion_control, args.reset, args.tcp_slow_start_after_idle,
            args.tcp_no_metrics_save, args.tcp_sack, args.tcp_recovery, args.tcp_wmem_min,
            args.tcp_wmem_default, args.tcp_wmem_max, args.tcp_rmem_min, args.tcp_rmem_default,
            args.tcp_rmem_max, args.tcp_fastopen, args.core_wmem_default, args.core_wmem_max,
            args.core_rmem_default, args.core_rmem_max, args.beta, args.fast_convergence,
            args.hystart_ack_delta, args.hystart_low_window, args.tcp_friendliness,
            args.hystart, args.hystart_detect, args.initial_ssthresh,
            interface=args.interface, route=route, scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()

