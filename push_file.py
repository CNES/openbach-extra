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
   
   
   
   @file     push_file.py
   @brief    Call the openbach-function push_file
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import argparse
from frontend import push_file, pretty_print


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(description='OpenBach - Push File',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('local_path', help='Path of the file in the Controller')
    parser.add_argument('remote_path', help='Path where the file should be pushed')
    parser.add_argument('agent_ip', help='IP address of the Agent')
    
    # get args
    args = parser.parse_args()
    local_path = args.local_path
    remote_path = args.remote_path
    agent_ip = args.agent_ip

    pretty_print(push_file)(local_path, remote_path, agent_ip)

