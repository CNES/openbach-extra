#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

""" Helpers of configure_link job """

def configure_link_apply_delay(
        scenario, entity, interface, mode, delay_distribution, delay, jitter=None,
        buffer_size=10000, wait_finished=None, wait_launched=None, wait_delay=0):
    function = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    apply_params = {'mode':mode,
                    'delay_distribution':delay_distribution,
                    'delay':delay,
                    'buffer_size':buffer_size}
    if jitter:
       apply_params.update({'jitter':jitter})
    function.configure(
            'configure_link', entity,
            interface_name=interface, 
            apply=apply_params)

    return [function]

def configure_link_apply_loss(
        scenario, entity, interface, mode, loss_model, loss_model_params,
        wait_finished=None, wait_launched=None, wait_delay=0):
    function = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    function.configure(
            'configure_link', entity,
            interface_name=interface, 
            apply={'mode':mode, 'loss_model':loss_model, 'loss_model_params':loss_model_params})
 
    return [function]

def configure_link_apply(
        scenario, entity, interface, mode, bandwidth=None, delay_distribution='normal', delay=0, jitter=0, 
        loss_model='random', loss_model_params=[0.0], buffer_size=10000, wait_finished=None,
        wait_launched=None, wait_delay=0):
    function = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    
    apply_params={'mode':mode,
                  'delay_distribution':delay_distribution,
                  'delay':delay,
                  'jitter':jitter,
                  'loss_model':loss_model,
                  'loss_model_params':loss_model_params,
                  'buffer_size':buffer_size
                 }
    if bandwidth:
       apply_params.update({'bandwidth':bandwidth})
    function.configure(
            'configure_link', entity,
            interface_name=interface, 
            apply=apply_params)
 
    return [function]

def configure_link_clear(
        scenario, entity, interface, mode, wait_finished=None, 
        wait_launched=None, wait_delay=0):
    function = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    function.configure(
            'configure_link', entity,
            interface_name=interface, 
            clear={'mode':mode})

    return [function]

def terrestrial_link(
        scenario, server, server_iface, server_bandwidth,
        client, client_iface, mode, client_bandwidth, delay_distribution, delay, jitter, 
        loss_model, loss_model_params,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'configure_link', server, offset=0,
            interface_name=server_iface,
            apply={'mode':mode, 'bandwidth':server_bandwidth, 
                   'delay_distribution':delay_distribution, 'delay':delay, 
                   'loss_model': loss_model, 'loss_model_params':loss_model_params})

    client = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    client.configure(
            'configure_link', client, offset=0,
            interface_name=client_iface,
            apply={'mode':mode, 'bandwidth':client_bandwidth, 
                   'delay_distribution':delay_distribution, 'delay':delay, 
                   'loss_model': loss_model, 'loss_model_params':loss_model_params})

    return [client, server]
