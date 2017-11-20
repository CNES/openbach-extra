#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.


"""Sources of the Job post_processing_tcp_pep"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import syslog
import argparse
from sys import exit

import collect_agent
from data_access import (
        CollectorConnection, ConditionTimestamp,
        ConditionAnd, Operator,
)


def main(collector, port, begin, end, simu_name, database_name):
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/post_processing_tcp_pep/'
            'post_processing_tcp_pep_rstats_filter.conf')
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)

    collector = CollectorConnection('localhost', influxdb_port=port)
    scenarios = collector.scenarios(
            job_name='pep', scenario_instance_id=simu_name,
            condition=ConditionAnd(
                ConditionTimestamp(Operator('>='), begin),
                ConditionTimestamp(Operator('<='), end)))

    for scenario in scenarios:
        for job in scenario.own_jobs:
            statistics = job.statistics
            timestamp = max(statistics.dated_data)
            count = len(statistics.dated_data)
            mean = sum(data['value'] for data in statistics.dated_data) / count
            collect_agent.send_stat(
                    timestamp, stat_name='???',
                    mean=mean, count=count)


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description='Calculation of mean interval for the simulation.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            'collector', metavar='collector',
            help='IP address of the collector')
    parser.add_argument(
            '-p', '--port', type=int, default=8086,
            help='port of the collector')
    parser.add_argument(
            '-b', '--begin', type=int, default=0,
            help='timestamp of the begin to look in ms')
    parser.add_argument(
            '-e', '--end', type=int, default=0,
            help='timestamp of the end to look in ms')
    parser.add_argument(
            '-s', '--simu-name', type=str, default='client',
            help='name of the simulation')
    parser.add_argument(
            '-d', '--database-name', type=str, default='openbach',
            help='name of the database')

    # get args
    args = parser.parse_args()
    collector = args.collector
    port = args.port
    begin = args.begin
    end = args.end
    simu_name = args.simu_name
    database_name = args.database_name

    main(collector, port, begin, end, simu_name, database_name)
