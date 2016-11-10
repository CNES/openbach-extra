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
   
   
   
   @file     set_job_stat_policy.py
   @brief    Call the openbach-function set_job_stat_policy
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import argparse
from frontend import set_job_stat_policy, date_to_timestamp, pretty_print


class DateMetavarHelper:
    def __init__(self):
        self.first = False

    def __repr__(self):
        self.first = not self.first
        return 'DATE' if self.first else 'TIME'


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(description='OpenBach - Update Job\'s stats Policy',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('agent_ip', help='IP Address of the Agent')
    parser.add_argument('job_name', help='Name of the Job')
    parser.add_argument('-n', '--stat-name', default=None, help='')
    parser.add_argument('-s', '--storage', action='store_true', help='')
    parser.add_argument('-b', '--broadcast', action='store_true', help='')
    parser.add_argument('-de', '--delete', action='store_true', help='')
    parser.add_argument('-d', '--date', metavar=DateMetavarHelper(),
                        nargs=2, help='Date of the execution')
    
    # get args
    args = parser.parse_args()
    agent_ip = args.agent_ip
    job_name = args.job_name
    stat_name = args.stat_name
    storage = args.storage
    broadcast = args.broadcast
    delete = args.delete
    if delete:
        storage = None
        broadcast = None
    date = date_to_timestamp('{} {}'.format(*args.date)) if args.date else None

    pretty_print(set_job_stat_policy)(agent_ip, job_name, stat_name, storage,
                                      broadcast, date)

