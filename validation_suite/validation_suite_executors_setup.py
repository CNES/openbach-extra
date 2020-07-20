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
        to list the project 
    delete_project : 
        to delete the project 
    list_project : 
        to list the project and check that the delete was ok
    create_project : 
        to create the project
    add_entity : 
        to add the entities to the project
    install_jobs : 
        to install the required jobs to the entities
"""

from auditorium_scripts.scenario_observer import ScenarioObserver
from auditorium_scripts.list_projects import ListProjects
from auditorium_scripts.delete_project import DeleteProject
from auditorium_scripts.create_project import CreateProject
from auditorium_scripts.install_jobs import InstallJobs
from auditorium_scripts.uninstall_jobs import UninstallJobs
from auditorium_scripts.add_entity import AddEntity

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


    print('======================================')
    print('Create project                        ') 
    print('======================================')
    # List the projects
    list_projects = observer._share_state(ListProjects)
    l_projects = list_projects.execute()
    # Check if the project exists and delete it if this is the case
    for s in l_projects:
        if any (args.project_name) in s: 
            # Delete the project
            delete_project = observer._share_state(DeleteProject)
            delete_project.args.name = args.project_name
            delete_project.execute()
            # List the projects
            list_projects = observer._share_state(ListProjects)
            list_projects.execute()

    # Create the project
    create_project = observer._share_state(CreateProject)
    create_project.args.project = {
            'name': args.project_name,
            'description': ' ',
            'owner': 'openbach',
    }
    create_project.execute()
    print('Project '+args.project_name+' created')

    print('======================================')
    print('Add entities to the project           ')
    print('======================================')
    # Add WSS entity to the project
    add_entity = observer._share_state(AddEntity)
    add_entity.args.entity_name = args.wss_entity
    add_entity.args.project_name = args.project_name
    add_entity.args.agent = args.wss_admin_ip
    add_entity.args.description = ' '
    add_entity.execute()
    # Add WSC entity to the project
    add_entity.args.entity_name = args.wsc_entity
    add_entity.args.project_name = args.project_name
    add_entity.args.agent = args.wsc_admin_ip
    add_entity.args.description = ' '
    add_entity.execute()
    # Add MIDBOX entity to the project
    add_entity.args.entity_name = args.midbox_entity
    add_entity.args.project_name = args.project_name
    add_entity.args.agent = args.midbox_admin_ip
    add_entity.args.description = ' '
    add_entity.execute()
    print(args.wss_entity+', '+args.wsc_entity+' and '+args.midbox_entity+' are added to '+args.project_name)

    print('======================================================')
    print('Install the specified jobs to entities')
    print('------------------------------------------------------')
    print('You may need to run')
    print('validation_suite_executors_setup_jobs_on_controller.sh')
    print('to add the required job on the controller')
    print('======================================================')
    # Install the jobs on WSS
    job_list = args.wss_jobs.split(',')
    for j in job_list:
        print(' ')
        print('Installing '+str(j)+' on '+args.wss_entity)
        uninstall_jobs = UninstallJobs()
        uninstall_jobs.parse(str('-j '+j+' -a '+args.wss_admin_ip).split())
        uninstall_jobs.execute()
        install_jobs = InstallJobs()
        install_jobs.parse(str('-j '+j+' -a '+args.wss_admin_ip).split())
        install_jobs.execute()
    # Install the jobs on WSC
    job_list = args.wsc_jobs.split(',')
    for j in job_list:
        print(' ')
        print('Installing '+str(j)+' on '+args.wsc_entity)
        uninstall_jobs = UninstallJobs()
        uninstall_jobs.parse(str('-j '+j+' -a '+args.wsc_admin_ip).split())
        uninstall_jobs.execute()
        install_jobs = InstallJobs()
        install_jobs.parse(str('-j '+j+' -a '+args.wsc_admin_ip).split())
        install_jobs.execute()
    # Install the jobs on MIDBOX
    job_list = args.midbox_jobs.split(',')
    for j in job_list:
        print(' ')
        print('Installing '+str(j)+' on '+args.midbox_entity)
        uninstall_jobs = UninstallJobs()
        uninstall_jobs.parse(str('-j '+j+' -a '+args.midbox_admin_ip).split())
        uninstall_jobs.execute()
        install_jobs = InstallJobs()
        install_jobs.parse(str('-j '+j+' -a '+args.midbox_admin_ip).split())
        install_jobs.execute()

if __name__ == '__main__':
    main()
