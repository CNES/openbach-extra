#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2019 CNES
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
#  Author: Nicolas Kuhn / <nicolas.kuhn@cnes.fr>

"""
This script is part of the OpenBACH validation suite. 
This script can run all available executors - or a sub set of them
The available entities are :

+------------+    +---------------+    +------------+    +-------------+
|wss_admin_ip|    |midbox_admin_ip|    |wsc_admin_ip|    |ctrl_admin_ip|
+------------+    +---------------+    +------------+    +-------------+
|entity:     |    |entity:        |    |entity:     |    |             | 
| wss        |    | midbox        |    |  wsc       |    |             |
+------------+    +---------------+    +------------+    +-------------+
|      wss_ip|    |midbox_ip_wss  |    |            |    |             |
|      wss_if|    |midbox_if_wss  |    |            |    |             |
|            |    |  midbox_ip_wsc|    |wsc_ip      |    |             |
|            |    |  midbow_if_wsc|    |wsc_if      |    |             |
+------------+    +---------------+    +------------+    +-------------+

Using parameters, the script has the following options:
    - all : all the available executors will be tested
    - network : all the executor_network_* will be tested
    - transport : all the executor_transport_* will be tested
    - service : all the executor_service_* will be tested
    - my-executor : the specified executor will be tested

Whatever the parameter, the script start by setting up the route between 
    wss <-> midbox <-> wsc

"""

