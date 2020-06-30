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
#  Author: Emmanuel Dubois / <emmanuel.dubois@cnes.fr>

"""
Global auditorium-scripts test campaign definition for OpenBACH platform
This script is a draft reference testing auditorium_scripts tool
"""

# Global Python modules
import sys
import argparse
from datetime import datetime
import requests
import time
import json
#import matplotlib
#matplotlib.use('Agg')
#import matplotlib.pyplot as plt
#from scipy import stats
#import numpy as np
#from statsmodels.distributions.empirical_distribution import ECDF
#import os

# Tests main definition parameters

#all_tests=('project',) use for launching all
tests_campaigns={} # Tests campaigns containing tests_names(important to be sorted)
tests_functions={} # Test linked Function : Class or function
tests={} # All tests independent from campaign with name and parameters dictionary

# Global Launch test function with FrontendBase class test object
def launch_test(test,test_parameters,show_response_content=True):
    test.parse(test_parameters) #Parse test parameters
    res=test.execute(show_response_content)
    res.raise_for_status()
    return res

## OpenBACH auditorium_scripts modules Import and Definition
from auditorium_scripts.frontend import FrontendBase

## Collector
from auditorium_scripts.add_collector import AddCollector
from auditorium_scripts.assign_collector import AssignCollector
from auditorium_scripts.change_collector_address import ChangeCollectorAddress
from auditorium_scripts.delete_collector import DeleteCollector
from auditorium_scripts.get_collector import GetCollector
from auditorium_scripts.list_collectors import ListCollectors
from auditorium_scripts.modify_collector import ModifyCollector
from auditorium_scripts.state_collector import StateCollector

################################### Agent #####################################
from auditorium_scripts.install_agent import InstallAgent
from auditorium_scripts.list_agents import ListAgents
from auditorium_scripts.modify_agent import ModifyAgent
from auditorium_scripts.set_agent_log_severity import SetAgentLogSeverity
from auditorium_scripts.state_agent import StateAgent
from auditorium_scripts.uninstall_agent import UninstallAgent

# Agent global variables
global AGENTS_IP
global AGENTS_NAMES
AGENTS_IP = [] # Agents IPs List
AGENTS_NAMES =  [] # Agents Names List

# Return all agents names()
def get_agents_parameters(test_parameters):
    test = ListAgents()
    response=launch_test(test,test_parameters, False)
    data = response.json()
    agents_parameters={}
    agents_parameters['address'] = [job['address'] for job in data]
    agents_parameters['name'] = [job['name'] for job in data]
    return agents_parameters

# Return all agents names()
def print_list_agents(test_parameters):
    agents_lister = ListAgents()
    agents_lister.parse(test_parameters)
    response = agents_lister.execute(show_response_content=False)
    response.raise_for_status()  # Check that no 4XX or 5XX status code is returned
    data = response.json()
    names = [job['name'] for job in data]
    ips = [job['address'] for job in data]
    print(names)
    print(ips)

def state_agents(test_parameters):
    agents_parameters=get_agents_parameters(test_parameters)
    print(agents_parameters)

    pass

# Agent Campaign definition
tests_campaigns['agents'] = ('get_agents_parameters','list_agents','print_list_agents','state_agents')
tests_functions['agents'] = {
                'get_agents_parameters':get_agents_parameters,
                'list_agents': ListAgents(),
                'print_list_agents': print_list_agents,
                'state_agents':state_agents
              }
tests['get_agents_parameters']=[]
tests['list_agents']=[]
tests['print_list_agents']=[]
tests['state_agents']=[]

#######################          Jobs             ##############################
from auditorium_scripts.add_job import AddJob
from auditorium_scripts.delete_job import DeleteJob
from auditorium_scripts.get_job_help import GetJobHelp
from auditorium_scripts.get_job_stats import GetJobStats
from auditorium_scripts.install_jobs import InstallJobs
from auditorium_scripts.list_installed_jobs import ListInstalledJobs
from auditorium_scripts.list_job_instances import ListJobInstances
from auditorium_scripts.list_jobs import ListJobs
from auditorium_scripts.restart_job_instance import RestartJobInstance
from auditorium_scripts.set_job_log_severity import SetJobLogSeverity
from auditorium_scripts.set_job_stats_policy import SetJobStatsPolicy
from auditorium_scripts.start_job_instance import StartJobInstance
from auditorium_scripts.state_job import StateJob
from auditorium_scripts.status_job_instance import StatusJobInstance
from auditorium_scripts.stop_job_instance import StopJobInstance
from auditorium_scripts.uninstall_jobs import UninstallJob

# Return all Installed jobs name
def get_jobs_names(test_parameters):
    jobs_lister = ListJobs()
    response = launch_test(jobs_lister,test_parameters,False)
    data = response.json()
    names = [job['general']['name'] for job in data]
    names.sort()
    return names

def print_jobs_names(test_parameters):
    print(get_jobs_names(test_parameters))

def state_job(job_name,agent):
    state=True
    state_job=StateJob()
    state_job.parse([job_name,agent])
    res=state_job.execute(show_response_content=False)
    res.raise_for_status()
    data = res.json()
    s=data['install']['returncode']
    print(s)
    if s not in range(200, 300):
        state=False
    return state


def install_jobs_agents(jobs_names,agents_ips):
    install_jobs=[]
    # Boucle pour chaque job à installer sur tous les agents.
    #jobs_names=['iperf3','socat','youtube']
    #agents_ips=['192.168.3.242', '192.168.3.235']

    for i in range(len(jobs_names)):
        print("\n* Install du job ",jobs_names[i])
        for agent in agents_ips:
            #Check if job is installed for each agent
            print("Agent ip :",agent, end='')
            #state=state_job(jobs_names[i],agent)
            state=0
            if state:
                print(" : Job installed")
            else:
                #Create install job object
                print(" : Job installation")
                install_job=InstallJobs()
                command_install_job=[
                 #    '--controller', '172.20.34.41',  # Can be ommitted
                 #    '--login', 'openbach',           # if defined in the
                 #    '--password', 'openbach',        # 'controller' file
                ]+['-j']
                command_install_job.append(jobs_names[i])
                command_install_job+=['-a']+agents_ips
                install_job.parse(command_install_job)
                response = install_job.execute(show_response_content=False)

# Jobs Campaign definition
tests_campaigns['jobs'] = ('get_jobs_names','print_jobs_names')
tests_functions['jobs'] = {
                    'get_jobs_names':get_jobs_names,
                    'print_jobs_names':print_jobs_names
                    }
tests['get_jobs_names']=[]
tests['print_jobs_names']=[]

##################### Projects #################################################
# Project Import
from auditorium_scripts.add_project import AddProject
from auditorium_scripts.delete_project import DeleteProject
from auditorium_scripts.get_project import GetProject
from auditorium_scripts.list_projects import ListProjects
from auditorium_scripts.modify_project import ModifyProject
from auditorium_scripts.create_project import CreateProject
# Project global variables
PROJECT_NAME = 'testobach'
PROJECT_FILE =  'testobach.json'
PROJECT_FILE2 = 'testobach2.json'
# Project tests definition
tests_campaigns['project'] = ('create_project','get_project','delete_project','add_project','modify_project','delete_project')
tests_functions['project'] = {  'create_project': CreateProject(),
                'delete_project': DeleteProject(),
                'get_project': GetProject(),
                'add_project':AddProject(),
                'modify_project':ModifyProject()  }
tests['create_project']= [
    PROJECT_NAME,                  # Name of the project
    '-d', 'Test Description',     # Description project
    '-p'                           #Public or no
    ]
tests['delete_project']= [
    PROJECT_NAME                  # Name of the project
    ]
tests['get_project']= [
    PROJECT_NAME                  # Name of the project
    ]
tests['add_project']= [
    PROJECT_FILE                  # Name of the project
    ]
tests['modify_project']= [
    PROJECT_NAME,      # Name of the project
    PROJECT_FILE2      # Other file of the project
    ]


# Scenario
from auditorium_scripts.create_scenario import CreateScenario
from auditorium_scripts.delete_scenario import DeleteScenario
from auditorium_scripts.get_scenario import GetScenario
from auditorium_scripts.list_scenarios import ListScenarios
from auditorium_scripts.modify_scenario import ModifyScenario
# Scenario/project information
SCENARIO_NAME = 'testobach'
SCENARIO_JSON_FILENAME = '{}.json'.format(SCENARIO_NAME)
SCENARIO_DESC = 'Testobach test'
OVERRIDE = True  # Override existing scenario with the same name
#
import scenario_builder as sb
scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_DESC)

def get_scenario(project_name, scenario_name):
    try:
        get = GetScenario()
        get.parse(['--project', project_name, scenario_name])
        r = get.execute()
    except requests.exceptions.HTTPError as ex:
        return False
    else:
        return True

def create_scenario(project_name, scenario_file):
    try:
        create = CreateScenario()
        create.parse(['--project', project_name, scenario_file])
        r = create.execute()
        r.raise_for_status()
        print('Scenario {} has been successfully created in the project {}.'.format(SCENARIO_NAME, PROJECT_NAME))
    except requests.exceptions.HTTPError as ex:
        raise ValueError('Error creating scenario' + ex)


def start_scenario_instance(project_name, scenario_name):
    start = StartScenarioInstance()
    start.parse(['--project', project_name , scenario_name])
    response = start.execute(False)
    try:
        scenario_id = response.json()['scenario_instance_id']
        print("Scenario instance id: ", scenario_id)
    except KeyError as ex:
        raise KeyError('Error starting scenario instance' + ex)
    except ValueError:
        raise ValueError('Error starting scenario instance' + ex)

    return scenario_id

# Scenario instance
from auditorium_scripts.delete_scenario_instances import DeleteScenarioInstances
from auditorium_scripts.list_scenario_instances import ListScenarioInstances
from auditorium_scripts.start_scenario_instance import StartScenarioInstance
from auditorium_scripts.status_scenario_instance import StatusScenarioInstance
from auditorium_scripts.stop_scenario_instance import StopScenarioInstance

# Push File
from auditorium_scripts.push_file import PushFile
from auditorium_scripts.state_push_file import StatePushFile

# Kill all
from auditorium_scripts.kill_all import KillAll

# ScenarioObserver
from auditorium_scripts.scenario_observer import ScenarioObserver

# OpenBACH scenario_builder import
from scenario_builder import Scenario

# OpenBACH data_access
from data_access import CollectorConnection

def launch_test_campaign(test_campaign_name):
    # Colors for Terminal Printing
    CRED = '\033[91m'
    CEND = '\033[0m'
    print("\t # Test campaign : "+CRED+test_campaign_name+CEND+" #")

    #Loop on all project scripts tests
    for test_name in tests_campaigns[test_campaign_name]:
        test=tests_functions[test_campaign_name][test_name]
        if(isinstance(test,FrontendBase)):
            print ("\n## Class Test "+CRED+test_name+CEND)
            launch_test(test,tests[test_name]) #Launch with object and parameters
        else:
            print ("\n## Function Test "+CRED+test_name+CEND)
            test(tests[test_name]) # Launch function with parameters
            pass

if __name__ == '__main__':
    #Check arguments and add help with argparse
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('test_campaign_name', choices=tests_campaigns.keys(), help="Names of the test campaign to launch. ")
    args = parser.parse_args()
    # Launch Test Campaign name with good argument
    launch_test_campaign(args.test_campaign_name)
