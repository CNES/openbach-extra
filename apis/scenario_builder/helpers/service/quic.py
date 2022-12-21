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

""" Helpers of quic job """

from ..utils import filter_none

def quic(
       scenario, server_entity, server_ip, server_port, server_implementation, 
       client_entity, client_implementation, resources, nb_runs, download_dir=None,
       server_log_dir=None, server_extra_args=None, client_log_dir=None, client_extra_args=None, 
       wait_finished=None, wait_launched=None, wait_delay=0):
    f_start_server = scenario.add_function(
                'start_job_instance',
                wait_finished=wait_finished,
                wait_launched=wait_launched,
                wait_delay=wait_delay)
    parameters = filter_none(
                implementation=server_implementation, 
                server_port=server_port,
                log_dir=server_log_dir,
                extra_args=server_extra_args)
    parameters['server'] = {}
    f_start_server.configure(
                'quic', server_entity, offset=0,
                **parameters
    )
    
    f_start_client = scenario.add_function(
                'start_job_instance',
                wait_launched=[f_start_server],
                wait_delay=5
    )
    parameters = filter_none(
                implementation=client_implementation,
                server_port=server_port,
                log_dir=client_log_dir,
                extra_args=client_extra_args)
    parameters['client'] = filter_none(
                server_ip=server_ip,
                resources=resources,
                download_dir=download_dir,
                nb_runs=nb_runs)
                
    f_start_client.configure(
                'quic', client_entity, offset=0,
                **parameters
    )               
    
    f_stop_server = scenario.add_function('stop_job_instance', wait_finished=[f_start_client])
    f_stop_server.configure(f_start_server)    
     
    return [f_start_server]   


def quic_server(
        scenario, server_entity, server_implementation, server_port, log_dir=None, 
        extra_args=None, wait_finished=None, wait_launched=None, wait_delay=0):
    f_start_server = scenario.add_function(
                'start_job_instance',
                wait_launched=wait_launched,
                wait_fininshed=wait_finished,
                wait_delay=wait_delay
    )
    parameters = filter_none(
                implementation=server_implementation,
                server_port=server_port,
                log_dir=log_dir,
                extra_args=extra_args)
    parameters['server'] = {}
                
    f_start_server.configure(
                'quic', server_entity, offset=0,
                **parameters
    )               
    
    return [f_start_server] 



def quic_client(
        scenario, server_ip, server_port, client_entity, client_implementation, resources, 
        nb_runs, download_dir=None, log_dir=None, extra_args=None, 
        wait_finished=None, wait_launched=None, wait_delay=0):
    f_start_client = scenario.add_function(
                'start_job_instance',
                wait_launched=wait_launched,
                wait_fininshed=wait_finished,
                wait_delay=wait_delay
    )
    parameters = filter_none(
                implementation=client_implementation,
                server_port=server_port,
                log_dir=log_dir,
                extra_args=extra_args)
    parameters['client'] = filter_none(
                server_ip=server_ip,
                resources=resources,
                download_dir=download_dir,
                nb_runs=nb_runs)
                
    f_start_client.configure(
                'quic', client_entity, offset=0,
                **parameters
    )               
    
    return [f_start_client]

 
def quic_find_client(openbach_function):
    return 'client' in openbach_function.start_job_instance['quic']
