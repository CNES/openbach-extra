#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
   
   
   
   @file     state_job.py
   @brief    Call the openbach-function state_job
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import argparse
from frontend import state_job, pretty_print


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(description='OpenBach - ',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('address', help='IP address of the Agent')
    parser.add_argument('name', help='Name of the Job')

    # get args
    args = parser.parse_args()

    pretty_print(state_job)(args.address, args.name)

