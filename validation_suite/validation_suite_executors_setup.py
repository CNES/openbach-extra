#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2019 CNES
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
#  Author: Nicolas Kuhn / <nicolas.kuhn@cnes.fr>

"""
This script is part of the OpenBACH validation suite. 
This script sets up the OpenBACH project using auditorium scripts. 
The available entities are : 

+------------+    +---------------+    +------------+    +-------------+
|wss_admin_ip|    |midbox_admin_ip|    |wsc_admin_ip|    |ctrl_admin_ip|
+------------+    +---------------+    +------------+    +-------------+
|entity:     |    |entity:        |    |entity:     |    |             | 
| wss        |    | midbox        |    |  wsc       |    |             |
+------------+    +---------------+    +------------+    +-------------+
|      wss_ip|    |midbox_ip_wss  |    |            |    |             |
|      wss_if|    |midbox_if_wss  |    |            |    |             |
|            |    |  midbox_ip_wsc|    |wsc_ip      |    |             |
|            |    |  midbow_if_wsc|    |wsc_if      |    |             |
+------------+    +---------------+    +------------+    +-------------+

This script exploits the following auditorium scripts: 

    list_project : 
        to list the project and see if the requested project is already created
    delete_project : 
        to delete the project if previously already created
    create_project : 
        to create the project
    add_entity : 
        to add the entities to the project
    install_jobs : 
        to install the required jobs to the entities
        uninstall_jobs : 
            to uninstall the jobs before the installation
        delete_job : 
            to remove the job from the controller
        add_job : 
            to add the job to the controller
        install_jobs : 
            to install the jobs
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from auditorium_scripts.list_projects import ListProjects
from auditorium_scripts.add_project import AddProject
from auditorium_scripts.delete_project import DeleteProject
from auditorium_scripts.create_project import CreateProject

def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--wss-entity', '-wss-e', required=True,
            help='Name of the WSS entity')
    observer.add_scenario_argument(
            '--wsc-entity', '-wsc-e', required=True,
            help='Name of the WSC entity')
    observer.add_scenario_argument(
            '--midbox-entity', '-m-e', required=True,
            help='Name of the WSS entity')
    observer.add_scenario_argument(
            '--wss-admin-ip', '-wss-ip', required=True,
            help='Admin IP address for the WSS entity')
    observer.add_scenario_argument(
            '--wsc-admin-ip', '-wsc-ip', required=True,
            help='Admin IP address for the WSC entity')
    observer.add_scenario_argument(
            '--midbox-admin-ip', '-m-ip', required=True,
            help='Admin IP address for the MidBox entity')
    observer.add_scenario_argument(
            '--wss-jobs', '-wss-j', required=True,
            help='Jobs to install on WSS'
                '"None" if no supplementary job'
                'Separated with commas if more than one job to install')
    observer.add_scenario_argument(
            '--wsc-jobs', '-wsc-j', required=True,
            help='Jobs to install on WSC'
                '"None" if no supplementary job'
                'Separated with commas if more than one job to install')
    observer.add_scenario_argument(
            '--midbox-jobs', '-m-j', required=True,
            help='Jobs to install on MidBox'
                '"None" if no supplementary job'
                'Separated with commas if more than one job to install')

    args = observer.parse(argv)

    # Create and add the project if the specified project does not exist 
    list_projects = observer._share_state(ListProjects)
    list_projects.execute()

    create_project = observer._share_state(CreateProject)
    create_project.parse([args.project_name])
    create_project.execute()

    # Add the entities to the project

    # Install the specified jobs on the entities

if __name__ == '__main__':
    main()
