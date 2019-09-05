#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

"""This script launches the *network_one_way_delay* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_one_way_delay


def main(scenario_name='generate_network_one_way_delay', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', required=True,
            help='name of the entity for the client of the RTT tests')
    observer.add_scenario_argument(
            '--server', '--server-entity', required=True,
            help='name of the entity for the server of the owamp RTT test')
    observer.add_scenario_argument(
            '--ip_dst', required=True, help='server ip address and target of owamp test')
    observer.add_scenario_argument(
            '--entity_pp', help='The entity where the post-processing will be '
            'performed (histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, scenario_name)

    scenario = network_one_way_delay.build(
                      args.client,
                      args.server,
                      args.ip_dst,
                      args.entity_pp)

    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
