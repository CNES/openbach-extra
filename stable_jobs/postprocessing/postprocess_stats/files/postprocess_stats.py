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


"""Sources of the Job postprocess_stats"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * David PRADAS <david.pradas@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import time
import syslog
import argparse
from sys import exit

# import matplotlib
# Force matplotlib to not use any Xwindows backend.
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt
from scipy import stats

import collect_agent
from data_access import CollectorConnection


def main(scenario_id, agent_name, job_ids, job_name, stat_name):
    # Connect to the collect-agent service
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/postprocess_stats/'
            'postprocess_stats_rstats_filter.conf')
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)

    requester = CollectorConnection('localhost')
    for job_instance_id in job_ids:
        # Import results from Collector Database
        try:
            scenario, = requester.scenarios(
                    job_name, scenario_id,
                    agent_name, job_instance_id)
        except Exception as ex:
            collect_agent.send_log(
                    syslog.LOG_ERR,
                    'Error getting stats from collector {}'.format(ex))
            continue

        job_key = (job_name, job_instance_id, agent_name)
        job_data = scenario.job_instances[job_key]
        statistics = [stat[stat_name] for stat in job_data.statistics.json()]

        # Compute mean statistics values (mean/std/etc)
        n, min_max, mean, var, skew, kurt = stats.describe(statistics)
        std = var**0.5
        confidence_interval = stats.norm.interval(
                0.9, loc=mean, scale=std/(len(statistics)**0.5))

        # Send stats mean/var/and ci to Collector
        timestamp = round(time.time() * 1000)
        statistics = {
                'mean_value_of_' + stat_name: mean,
                'variance_value_of_' + stat_name: var,
                'down_ci_value_of_' + stat_name: confidence_interval[0],
                'up_ci_value_of_' + stat_name: confidence_interval[1],
        }
        try:
            collect_agent.send_stat(timestamp, **statistics)
        except Exception as ex:
            collect_agent.send_log(
                    syslog.LOG_ERR,
                    'ERROR sending stats {}'.format(ex))

        # Compute, plot and save figure of CDF
        # try:
        #     plt.figure(figsize=(12, 8), dpi=80, facecolor='w', edgecolor='k')
        # except Exception as ex:
        #     collect_agent.send_log(
        #             syslog.LOG_ERR,
        #             'Matplotlib problem: {}'.format(ex))

        # plt.ylabel('CDF')
        # plt.xlabel('Page load time (s)')
        # plt.title('CDF of web page load time')
        # n, bins, patches = plt.hist(statistics, 1000, normed=1, cumulative=True)

        # path = '/tmp/cdf_{}_{}_{}_{}.png'.format(
        #         scenario_id, job_instance_id,
        #         job_name, stat_name)
        # try:
        #     plt.savefig(path)
        #     collect_agent.send_log(
        #             syslog.LOG_DEBUG,
        #             'Plot file saved in {}'.format(path))
        # except Exception as ex:
        #     collect_agent.send_log(
        #             syslog.LOG_ERR,
        #             'Error saving plot files {}'.format(ex))


if __name__ == '__main__':
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            'scenario_instance_id', type=int,
            help='The ID of the scenario instance where the stat can be found')
    parser.add_argument(
            'agent_name',
            help='The agent name where the stat has been generated')
    parser.add_argument(
            'job_name', help='The job name that has generated the stat')
    parser.add_argument(
            'stat_name',
            help='The name of the stat that shall be postprocessed')
    parser.add_argument(
            'job_instance_ids', nargs='+', type=int,
            help='The IDs of the job instances that have '
            'generated the stat')
    parser.add_argument(
            '-m', '--export-mode',
            type=int, help='The type of export')

    # get args
    args = parser.parse_args()
    scenario_id = args.scenario_instance_id
    agent_name = args.agent_name
    job_ids = args.job_instance_ids
    job_name = args.job_name
    stat_name = args.stat_name
    # export_mode = args.export_mode

    main(scenario_id, agent_name, job_ids, job_name, stat_name)
