#!/usr/bin/env python3

""" 
   OpenBACH is a generic testbed able to control/configure multiple
   network/physical entities (under test) and collect data from them. It is
   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
   Agents (one for each network entity that wants to be tested).
   
   
   Copyright © 2016 CNES
   
   
   This file is part of the OpenBACH testbed.
   
   
   OpenBACH is a free software : you can redistribute it and/or modify it under the
   terms of the GNU General Public License as published by the Free Software
   Foundation, either version 3 of the License, or (at your option) any later
   version.
   
   This program is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
   details.
   
   You should have received a copy of the GNU General Public License along with
   this program. If not, see http://www.gnu.org/licenses/.
   
   
   
   @file     start_job_instance.py
   @brief    Call the openbach-function start_job_instance
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import argparse
import pprint
import shlex
from frontend import start_job_instance, status_job_instance, date_to_timestamp, pretty_print


class DateMetavarHelper:
    def __init__(self):
        self.first = False

    def __repr__(self):
        self.first = not self.first
        return 'DATE' if self.first else 'TIME'


def main(agent_ip, job_name, arguments, date, interval, status=None):
    response = start_job_instance(agent_ip, job_name, arguments, date, interval)
    print('Start Instance:')
    print(response)
    infos = response.json()
    pprint.pprint(infos)

    if status is not None:
        instance_id = int(infos['instance_id'])
        print('Start watch of the status:')
        pretty_print(status_job_instance)(instance_id, interval=status)


if __name__ == "__main__":
    def parse(value):
        name, *values = shlex.split(value, posix=True)
        return name, values

    # Define Usage
    parser = argparse.ArgumentParser(description='OpenBach - Start and Status Instance',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('agent_ip', help='IP address of the Agent')
    parser.add_argument('job_name', help='Name of the Job')
    parser.add_argument('-s', '--status', help='Start a watch of the status with this interval')
    parser.add_argument('-a', '--argument', type=parse, nargs='+',
                        metavar='NAME[ VALUE[ VALUE...]]')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-d', '--date', metavar=DateMetavarHelper(),
                        nargs=2, help='Date of the execution')
    group.add_argument('-i', '--interval', help='Interval of the execution')

    # get args
    args = parser.parse_args()
    agent_ip = args.agent_ip
    job_name = args.job_name
    if type(args.argument) == list:
        arguments = dict(args.argument)
    else:
        arguments = {}
    date = date_to_timestamp('{} {}'.format(*args.date)) if args.date else None
    interval = args.interval
    status = args.status

    main(agent_ip, job_name, arguments, date, interval, status)

