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

"""Helpers of d-itg_send and d-itg_receiv jobs"""


#   Important Note :
#   The accuracy of D-ITG as rate measurement tool has not been proved yet.
#   Its usage is in experimental phase.


def ditg_packet_rate(
        scenario, sender_entity, recv_entity, recv_ip, sender_ip, protocol,
        dest_path="/tmp/", granularity=1000, packet_size=512,
        packet_rate=1000, duration=10, meter="owdm", log_buffer_size=50,
        port=8999, signal_port=9000,
        wait_finished=None, wait_launched=None, wait_delay=0):
    
    recv = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    recv.configure(
            'd-itg_recv', recv_entity,
            log_buffer_size=log_buffer_size,
            signal_port=signal_port)

    sender = scenario.add_function(
            'start_job_instance', 
            wait_launched=[recv],
            wait_delay=1)
    sender.configure(
            'd-itg_send', sender_entity,
            target_address=recv_ip,
            sender_address=sender_ip,
            dest_path=dest_path,
            granularity=granularity,
            traffic_type=protocol,
            packet_size=packet_size,
            packet_rate=packet_rate,
            port=port,
            signal_port=signal_port,
            duration=duration,
            meter=meter)
    
    stop_recv = scenario.add_function('stop_job_instance', wait_finished=[sender])
    stop_recv.configure(recv)

    return [recv]


def ditg_rate(
        scenario, sender_entity, recv_entity, recv_ip, sender_ip, protocol,
        dest_path="/tmp/", granularity=1000, packet_size=512, rate="10M",
        duration=10, meter="rttm", log_buffer_size=50, port=8999, signal_port=9000,
        wait_finished=None, wait_launched=None, wait_delay=0):
    
    recv = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    recv.configure(
            'd-itg_recv', recv_entity,
            log_buffer_size=log_buffer_size,
            signal_port=signal_port)

    sender = scenario.add_function(
            'start_job_instance',
            wait_launched=[recv],
            wait_delay=1)
    sender.configure(
            'd-itg_send', sender_entity,
            target_address=recv_ip,
            sender_address=sender_ip,
            dest_path=dest_path,
            granularity=granularity,
            traffic_type=protocol,
            packet_size=packet_size,
            packet_rate=0, port=port,
            signal_port=signal_port,
            bandwidth=rate,
            duration=duration,
            meter=meter)

    stop_recv = scenario.add_function('stop_job_instance', wait_finished=[sender])
    stop_recv.configure(recv)

    return [recv]
