#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2020 CNES
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

"""Helpers of pep job"""

def pep(
        scenario, port, address, fastopen,
        maxconns, gcc_interval, log_file, pending_lifetime, 
        stop, redirect_ifaces, redirect_src_ip, 
        redirect_dst_ip, mark, table_num, 
        wait_finished=None, wait_launched=None, wait_delay=0):
    function = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    function.configure(
            'pep',
            port=port,
            address=address,
            fastopen=fastopen,
            maxconns=maxconns,
            gcc_interval=gcc_interval,
            log_file=log_file,
            pending_lifetime=pending_lifetime,
            stop=stop,
            redirect_ifaces=redirect_ifaces,
            redirect_src_ip=redirect_src_ip,
            redirect_dst_ip=redirect_dst_ip,
            mark=mark,
            table_num=table_num)

    return [function]

