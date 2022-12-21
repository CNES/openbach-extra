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

"""Helpers of tcp_conf_linux job"""

from ..utils import filter_none


def tcp_conf_linux(
        scenario, entity, congestion_control, reset=None, tcp_slow_start_after_idle=None,
        tcp_no_metrics_save=None, tcp_sack=None, tcp_recovery=None, tcp_wmem_min=None,
        tcp_wmem_default=None, tcp_wmem_max=None, tcp_rmem_min=None, tcp_rmem_default=None,
        tcp_rmem_max=None, tcp_fastopen=None, core_wmem_default=None, core_wmem_max=None,
        core_rmem_default=None, core_rmem_max=None, beta=None, fast_convergence=None,
        hystart_ack_delta=None, hystart_low_window=None, tcp_friendliness=None, hystart=None,
        hystart_detect=None, initial_ssthresh=None,
        wait_finished=None, wait_launched=None, wait_delay=0):

    function = scenario.add_function(
           'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)

    parameters = filter_none(
            reset=reset,
            tcp_slow_start_after_idle=tcp_slow_start_after_idle,
            tcp_no_metrics_save=tcp_no_metrics_save,
            tcp_sack=tcp_sack,
            tcp_recovery=tcp_recovery,
            tcp_wmem_min=tcp_wmem_min,
            tcp_wmem_default=tcp_wmem_default,
            tcp_wmem_max=tcp_wmem_max,
            tcp_rmem_min=tcp_rmem_min,
            tcp_rmem_default=tcp_rmem_default,
            tcp_rmem_max=tcp_rmem_max,
            tcp_fastopen=tcp_fastopen,
            core_wmem_default=core_wmem_default,
            core_wmem_max=core_wmem_max,
            core_rmem_default=core_rmem_default,
            core_rmem_max=core_rmem_max)

    if congestion_control.upper() == 'CUBIC':
        parameters['CUBIC'] = filter_none(
                beta=beta,
                fast_convergence=fast_convergence,
                hystart_ack_delta=hystart_ack_delta,
                hystart_low_window=hystart_low_window,
                tcp_friendliness=tcp_friendliness,
                hystart=hystart,
                hystart_detect=hystart_detect,
                initial_ssthresh=initial_ssthresh)
    else:
        parameters['other'] = {'congestion_control_name':congestion_control}

    function.configure('tcp_conf_linux', entity, **parameters)

    return [function]
