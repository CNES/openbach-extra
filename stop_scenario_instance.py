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
   
   
   
   @file     stop_scenario_instance.py
   @brief    Call the openbach-function stop_scenario_instance
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import argparse
from frontend import stop_scenario_instance, pretty_print, date_to_timestamp


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
    parser.add_argument('scenario_instance_id', help='Id of the scenario'
                        ' instance to stop') 
    parser.add_argument('-d', '--date', metavar=DateMetavarHelper(),
                        nargs=2, help='Date of the execution')
    parser.add_argument('-s', '--scenario-name', help='Name of the Scenario')
    parser.add_argument('-p', '--project-name', help='Name of the Project')

    # get args
    args = parser.parse_args()
    scenario_instance_id = args.scenario_instance_id
    date = date_to_timestamp('{} {}'.format(*args.date)) if args.date else None
    scenario_name = args.scenario_name
    project_name = args.project_name

    pretty_print(stop_scenario_instance)(scenario_instance_id, date,
                                         scenario_name, project_name)

