#!/bin/bash
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

#########################################################################
#This script is part of the OpenBACH validation suite. 
#This script sets up the OpenBACH project using auditorium scripts. 
#The available entities are : 
#
#+------------+    +---------------+    +------------+    +-------------+
#|wss_admin_ip|    |midbox_admin_ip|    |wsc_admin_ip|    |ctrl_admin_ip|
#+------------+    +---------------+    +------------+    +-------------+
#|entity:     |    |entity:        |    |entity:     |    |             | 
#| wss        |    | midbox        |    |  wsc       |    |             |
#+------------+    +---------------+    +------------+    +-------------+
#|      wss_ip|    |midbox_ip_wss  |    |            |    |             |
#|      wss_if|    |midbox_if_wss  |    |            |    |             |
#|            |    |  midbox_ip_wsc|    |wsc_ip      |    |             |
#|            |    |  midbow_if_wsc|    |wsc_if      |    |             |
#+------------+    +---------------+    +------------+    +-------------+
#
#This script exploits the following auditorium scripts: 
#
#    list_project : 
#    	to list the project and see if the requested project is already created
#    delete_project : 
#    	to delete the project if previously already created
#    create_project : 
#    	to create the project
#    add_entity : 
#    	to add the entities to the project
#    install_jobs : 
#	to install the required jobs to the entities
#########################################################################

project_name=$1
wss_entity=$2
wsc_entity=$3
midbox_entity=$4
wss_admin_ip=$5
wsc_admin_ip=$6
midbox_admin_ip=$7
wss_jobs=$8
wsc_jobs=$9
midbox_jobs=${10}

echo "======================================"
echo "Create project"
echo "======================================"
# List existing projects
l_projects=$(python3 ../apis/auditorium_scripts/list_projects.py) 
# Check if the project already exists
if [[ $l_projects =~ $project_name ]]
then 
	echo "The project already exists"
	echo "It will be deleted to create the new project"

	# Delete the project
	python3 ../apis/auditorium_scripts/delete_project.py $project_name
fi 
# Create the project
python3 ../apis/auditorium_scripts/create_project.py $project_name
echo "Project $project_name created"

echo "======================================"
echo "Add entities to project"
echo "======================================"
# Add WSS entity to the project
python3 ../apis/auditorium_scripts/add_entity.py -a $wss_admin_ip $wss_entity $project_name
# Add WSC entity to the project
python3 ../apis/auditorium_scripts/add_entity.py -a $wsc_admin_ip $wsc_entity $project_name 
# Add MIDBOX entity to the project
python3 ../apis/auditorium_scripts/add_entity.py -a $midbox_admin_ip $midbox_entity $project_name 

echo "$wss_entity , $wsc_entity and $midbox_entity are added to $project_name"

echo "======================================"
echo "Install the specified jobs to entities"
echo "======================================"
echo "You may need to run"
echo "validation_suite_executors_setup_jobs_on_controller.sh"
echo "to add the required job on the controller"
# Install the jobs on WSS
if [[ $wss_jobs != None ]]
then
	IFS=','
	read -ra JOB <<< "$wss_jobs"
	for i in "${JOB[@]}"; do
	        echo "Installing $i on $wss_entity"	
    		python3 ../apis/auditorium_scripts/uninstall_jobs.py -j $i -a $wss_admin_ip
    		python3 ../apis/auditorium_scripts/install_jobs.py -j $i -a $wss_admin_ip
	done
fi
# Install the jobs on WSC
if [[ $wsc_jobs != None ]]
then
	IFS=','
	read -ra JOB <<< "$wsc_jobs"
	for i in "${JOB[@]}"; do 
	        echo "Installing $i on $wsc_entity"	
    		python3 ../apis/auditorium_scripts/uninstall_jobs.py -j $i -a $wsc_admin_ip
    		python3 ../apis/auditorium_scripts/install_jobs.py -j $i -a $wsc_admin_ip
	done
fi
# Install the jobs on MIDBOX
if [[ $midbox_jobs != None ]]
then
	IFS=','
	read -ra JOB <<< "$midbox_jobs"
	for i in "${JOB[@]}"; do 
	        echo "Installing $i on $midbox_entity"	
    		python3 ../apis/auditorium_scripts/uninstall_jobs.py -j $i -a $midbox_admin_ip
    		python3 ../apis/auditorium_scripts/install_jobs.py -j $i -a $midbox_admin_ip
	done
fi
