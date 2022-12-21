#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2023 CNES
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

"""This executor builds or launches the *service_ftp_rate* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
Real Ftp server and client with download or upload of a file.
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import service_ftp

def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--server-entity', required=True,
            help='name of the entity for the FTP server')
    observer.add_scenario_argument(
            '--client-entity', required=True,
            help='name of the entity for the FTP client')
    observer.add_scenario_argument(
            '--server-ip', required=True, help='The server IP address')
    observer.add_scenario_argument(
            '--server-port', type=int, default=2121, help='Listened port')
    observer.add_scenario_argument(
            '--mode', required=True,
            choices=['upload', 'download'], help='upload or download')
    observer.add_scenario_argument(
            '--file-path', default='100M_file.txt', help='File path to transfer')
    observer.add_scenario_argument(
            '--multiple', type=int, default=1, help='Number of transfer of the file')
    observer.add_scenario_argument(
            '--ftp-user', default='openbach', help='Authorized FTP user')
    observer.add_scenario_argument(
            '--ftp-password', default='openbach', help="Authorized FTP user's password")
    observer.add_scenario_argument(
            '--blocksize', type=int, default=8192, help='Set maximum chunk size')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be '
            'performed (histogram/time-series jobs must be installed) if defined')

    args = observer.parse(argv, service_ftp.SCENARIO_NAME)

    scenario = service_ftp.build(
            args.server_entity,
            args.client_entity,
            args.server_ip,
            args.server_port,
            args.mode,
            args.file_path,
            args.multiple,
            args.ftp_user,
            args.ftp_password,
            args.blocksize,
            args.post_processing_entity,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
