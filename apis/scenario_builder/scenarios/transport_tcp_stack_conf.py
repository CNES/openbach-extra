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
from scenario_builder.helpers.transport.tcp_conf_linux import tcp_conf_linux
from scenario_builder.helpers.transport.ethtool import ethtool_disable_segmentation_offload
from scenario_builder.helpers.network.ip_route import ip_route
from inspect import signature

SCENARIO_NAME = 'transport_tcp_stack_conf'
SCENARIO_DESCRIPTION = """This *transport_tcp_stack_conf* scenario allows to configure:
 - TCP congestion control and associated parameters,
 - route including TCP parameters like initial congestion and receive windows
 - TCP segmentation offloading on a network interface.

If reset option is set, the sysctl and CUBIC parameters are reset to the value
they had at the installation of the job of tcp_conf_linux. Then the parameters
are updated only if a new value is set in the arguments. More information on
the wiki page of the job tcp_conf_linux.
"""

def tcp_stack_conf(entity, congestion_control, reset=None, tcp_slow_start_after_idle=None,
        tcp_no_metrics_save=None, tcp_sack=None, tcp_recovery=None, tcp_wmem_min=None,
        tcp_wmem_default=None, tcp_wmem_max=None, tcp_rmem_min=None, tcp_rmem_default=None,
        tcp_rmem_max=None, tcp_fastopen=None, core_wmem_default=None, core_wmem_max=None,
        core_rmem_default=None, core_rmem_max=None, beta=None, fast_convergence=None,
        hystart_ack_delta=None, hystart_low_window=None, tcp_friendliness=None,
        hystart=None, hystart_detect=None, initial_ssthresh=None,
        interface=None, route=None, scenario_name=SCENARIO_NAME):

    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    args = {'entity': entity, 'cc': congestion_control, 'interface': interface}
    if route:
        args.update(route)

    for arg, value in args.items():
        if str(value).startswith('$'):
            scenario.add_constant(arg, value[1:])

    tcp_conf_linux(scenario, entity, congestion_control, reset, tcp_slow_start_after_idle,
            tcp_no_metrics_save, tcp_sack, tcp_recovery, tcp_wmem_min,
            tcp_wmem_default, tcp_wmem_max, tcp_rmem_min, tcp_rmem_default,
            tcp_rmem_max, tcp_fastopen, core_wmem_default, core_wmem_max,
            core_rmem_default, core_rmem_max, beta, fast_convergence,
            hystart_ack_delta, hystart_low_window, tcp_friendliness,
            hystart, hystart_detect, initial_ssthresh)

    if interface:
        ethtool_disable_segmentation_offload(scenario, entity, interface)

    if route and route.get('destination_ip') is not None:
        operation = route.pop('operation', 'change')
        ip_route(scenario, entity, operation, **route)

    return scenario


def build(entity, congestion_control, reset=None, tcp_slow_start_after_idle=None,
        tcp_no_metrics_save=None, tcp_sack=None, tcp_recovery=None, tcp_wmem_min=None,
        tcp_wmem_default=None, tcp_wmem_max=None, tcp_rmem_min=None, tcp_rmem_default=None,
        tcp_rmem_max=None, tcp_fastopen=None, core_wmem_default=None, core_wmem_max=None,
        core_rmem_default=None, core_rmem_max=None, beta=None, fast_convergence=None,
        hystart_ack_delta=None, hystart_low_window=None, tcp_friendliness=None,
        hystart=None, hystart_detect=None, initial_ssthresh=None,
        interface=None, route=None, scenario_name=SCENARIO_NAME):

    return tcp_stack_conf(entity, congestion_control, reset, tcp_slow_start_after_idle,
            tcp_no_metrics_save, tcp_sack, tcp_recovery, tcp_wmem_min,
            tcp_wmem_default, tcp_wmem_max, tcp_rmem_min, tcp_rmem_default,
            tcp_rmem_max, tcp_fastopen, core_wmem_default, core_wmem_max,
            core_rmem_default, core_rmem_max, beta, fast_convergence,
            hystart_ack_delta, hystart_low_window, tcp_friendliness,
            hystart, hystart_detect, initial_ssthresh,
            interface, route, scenario_name)

