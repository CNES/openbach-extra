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
   
   
   
   @file     start_scenario_instance.py
   @brief    Call the openbach-function start_scenario_instance
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import argparse
import json
from frontend import start_scenario_instance, pretty_print, date_to_timestamp


class DateMetavarHelper:
    def __init__(self):
        self.first = False

    def __repr__(self):
        self.first = not self.first
        return 'DATE' if self.first else 'TIME'


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(description='OpenBach - Start a Scenario',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', help='Name of the scenario to start') 
    parser.add_argument('path', help='Path to the args of the scenario instance') 
    parser.add_argument('-d', '--date', metavar=DateMetavarHelper(),
                        nargs=2, help='Date of the execution')
    parser.add_argument('-p', '--project-name', help='Name of the Project')

    # get args
    args = parser.parse_args()
    name = args.name
    path = args.path
    date = date_to_timestamp('{} {}'.format(*args.date)) if args.date else None
    with open(path, 'r') as f:
        args_json = json.loads(f.read())
    project_name = args.project_name

    pretty_print(start_scenario_instance)(name, args_json, date, project_name)

