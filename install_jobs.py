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
   
   
   
   @file     install_jobs.py
   @brief    Call the openbach-function install_jobs
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


import argparse
import itertools
from frontend import install_jobs, pretty_print


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(description='OpenBach - Install Job')
    parser.add_argument('-j', '--job_name', metavar='NAME', action='append',
            nargs='+', required=True, help='Name of the Jobs to install on '
            'the next agent. May be specified several times to install '
            'different sets of jobs on different agents.')
    parser.add_argument('-a', '--agent_ip', metavar='ADDRESS', action='append',
            required=True, help='IP address of the agent where the next set '
            'of jobs should be installed. May be specified several times to '
            'install different sets of jobs on different agents.')
    
    # get args
    args = parser.parse_args()
    jobs_names = args.job_name
    agents_ips = args.agent_ip

    # If user specified more set of jobs than agent ips
    # we can't figure it out
    if len(jobs_names) != len(agents_ips):
        parser.error('-j and -a arguments should appear by pairs')

    # Backward compatibility: change the backend behaviour
    # before removing the next 4 lines
    #  -> flatten jobs_names so we have a list instead of a list of lists
    jobs_names = list(itertools.chain.from_iterable(jobs_names))
    #  -> use only the first agent ip
    agents_ips = [agents_ips[0]]

    pretty_print(install_jobs)(jobs_names, agents_ips)

