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

"""Helpers of skype job"""


def skype(
        scenario, receiver_entity, receiver_email_address, receiver_password,
        caller_entity, caller_email_address, caller_password, receiver_contact,
        call_type, duration, timeout,
        wait_finished=None, wait_launched=None, wait_delay=0):
    receive = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    receive.configure(
            'skype', receiver_entity, offset=0,
            email_address=receiver_email_address,
            password=receiver_password,
            call_type=call_type,
            timeout=timeout,
            receiver={})

    call = scenario.add_function(
            'start_job_instance',
            wait_launched=[receive],
            wait_delay=5)
    call.configure(
            'skype', caller_entity, offset=0,
            email_address=caller_email_address,
            password=caller_password,
            call_type=call_type,
            timeout=timeout,
            caller={
                'contact': receiver_contact,
                'call_duration': duration,
            })

    stop = scenario.add_function('stop_job_instance', wait_finished=[call])
    stop.configure(receive)

    return [receive]
