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

"""This scenario builds and launches the OpenSAND scenario
from /openbach-extra/apis/scenario_builder/scenarios/
"""


import tempfile
from argparse import FileType

from auditorium_scripts.scenario_observer import ScenarioObserver
from auditorium_scripts.push_file import PushFile


def main(scenario_name='opensand', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--address', '-a', required=True,
            help='Address of the agent to send files to')
    observer.add_scenario_argument(
            '--file', '-f', required=True,
            type=FileType('r'),
            help='File to transfert as /opt/openbach/agent/bite.txt')
    observer.add_scenario_argument(
            '--content', '-c', default='Empty file',
            help='Alternative content for /opt/openbach/agent/toto.txt')

    args = observer.parse(argv, scenario_name)

    pusher = observer._share_state(PushFile)
    pusher.args.keep = True

    pusher.args.local_file = args.file
    pusher.args.remote_path = '/opt/openbach/agent/bite.txt'
    pusher.execute(True)

    with tempfile.NamedTemporaryFile('w+') as f:
        print(args.content, file=f, flush=True)
        f.seek(0)

        pusher.args.local_file = f
        pusher.args.remote_path = '/opt/openbach/agent/toto.txt'
        pusher.execute(True)


if __name__ == '__main__':
    main()
