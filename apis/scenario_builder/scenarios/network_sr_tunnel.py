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

from scenario_builder import Scenario
from scenario_builder.openbach_functions import StartJobInstance

from scenario_builder.helpers.network.ip_route import ip_route
from scenario_builder.helpers.network.sr_tunnel import create_sr_tunnel
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph


SCENARIO_NAME = 'network_sr_tunnel'
SCENARIO_DESCRIPTION = """This scenario creates a SR tunnel between 2 entities.
It launches 'sr_tunnel' which is a program which implements a Selective Repeat
algorithm at the IP level within a TUN/TAP tunnel. A good illustration of
the algorithm implemented is given here :
https://www2.tkn.tu-berlin.de/teaching/rn/animations/gbn_sr/.

**Important Note** : the traffic needs to be sent to the 'tun0' interfaces in order to
activate the Selective Repeate process.
"""


def sr_tunnel(
        server_entity, client_entity, server_ip, server_tun_ip, client_tun_ip, server_port,
        trace, server_drop, client_drop, server_burst, client_burst, duration,
        scenario_name=SCENARIO_NAME):
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    scenario.add_constant('server_ip', server_ip)
    scenario.add_constant('server_tun_ip', server_tun_ip)
    scenario.add_constant('client_tun_ip', client_tun_ip)
    scenario.add_constant('trace', trace)

    tunnel = create_sr_tunnel(
            scenario, server_entity, client_entity, '$server_ip', '$server_tun_ip',
            '$client_tun_ip', server_port, '$trace', server_drop, client_drop,
            server_burst, client_burst)

    return scenario


def build(
        server_entity, client_entity, server_ip, server_tun_ip, client_tun_ip, server_port=None,
        trace=None, server_drop=None, client_drop=None, server_burst=None, client_burst=None, duration=0,
        scenario_name=SCENARIO_NAME):

    scenario = sr_tunnel(
            server_entity, client_entity, server_ip, server_tun_ip, client_tun_ip, server_port,
            trace, server_drop, client_drop, server_burst, client_burst, duration, scenario_name)

    if duration:
        jobs = [f for f in scenario.openbach_functions if isinstance(f, StartJobInstance)]
        scenario.add_function('stop_job_instance', wait_launched=jobs, wait_delay=duration).configure(*jobs)

    return scenario

