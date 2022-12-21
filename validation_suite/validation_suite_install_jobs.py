#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2023 CNES
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

"""Validation Suite

This module aims at being an exhaustive test of OpenBACH capabilities
to prevent regressions and help develop new features. Its role is to
run as much auditorium scripts has feasible and run a few scenarios
or executors.

The various tests will try to smartly understand the installed platform
it is run on to adequately select which tasks can be performed and on
which agent. The idea being to be unobtrusive in existing projects, this
means that on some platforms, agents can be already associated to a
project; so in order to get things tested, new machines can be associated
as agents for the time of the tests.
"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Mathias ETTINGER <mathias.ettinger@viveris.fr>
 * Bastien TAURAN <bastien.tauran@viveris.fr>
'''

import os
import sys
import time
import urllib3
import getpass
import logging
import textwrap
import tempfile
import itertools
import logging.config
from pathlib import Path
from random import sample
from collections import Counter

import pprint

from requests.compat import json

CWD = Path(__file__).resolve().parent
sys.path.insert(0, Path(CWD.parent, 'apis').as_posix())

from auditorium_scripts.frontend import FrontendBase, ActionFailedError
from auditorium_scripts.list_agents import ListAgents
from auditorium_scripts.list_collectors import ListCollectors
from auditorium_scripts.list_installed_jobs import ListInstalledJobs
from auditorium_scripts.list_jobs import ListJobs
from auditorium_scripts.list_projects import ListProjects
from auditorium_scripts.list_job_instances import ListJobInstances
from auditorium_scripts.install_agent import InstallAgent
from auditorium_scripts.uninstall_agent import UninstallAgent
from auditorium_scripts.add_collector import AddCollector
from auditorium_scripts.assign_collector import AssignCollector
from auditorium_scripts.delete_collector import DeleteCollector
from auditorium_scripts.add_project import AddProject
from auditorium_scripts.create_project import CreateProject
from auditorium_scripts.delete_project import DeleteProject
from auditorium_scripts.get_project import GetProject
from auditorium_scripts.modify_project import ModifyProject
from auditorium_scripts.add_entity import AddEntity
from auditorium_scripts.delete_entity import DeleteEntity
from auditorium_scripts.add_job import AddJob
from auditorium_scripts.install_jobs import InstallJobs
from auditorium_scripts.start_job_instance import StartJobInstance
from auditorium_scripts.status_job_instance import StatusJobInstance
from auditorium_scripts.state_job import StateJob
from auditorium_scripts.stop_job_instance import StopJobInstance
from auditorium_scripts.stop_all_job_instances import StopAllJobInstances
from auditorium_scripts.uninstall_jobs import UninstallJobs
from auditorium_scripts.delete_job import DeleteJob
from auditorium_scripts.add_scenario import AddScenario
from auditorium_scripts.create_scenario import CreateScenario
from auditorium_scripts.modify_scenario import ModifyScenario
from auditorium_scripts.start_scenario_instance import StartScenarioInstance
from auditorium_scripts.status_scenario_instance import StatusScenarioInstance
from auditorium_scripts.stop_scenario_instance import StopScenarioInstance
from auditorium_scripts.delete_scenario import DeleteScenario
from auditorium_scripts.get_scenario_instance_data import GetScenarioInstanceData

# TODO warning: with this script platform must be clean (or user agree to lose everything)
# TODO: agents must be installed


class ValidationSuite(FrontendBase):
    PASSWORD_SENTINEL = object()

    def __init__(self):
        super().__init__('OpenBACH − Validation Suite')
        self.parser.add_argument(
                '-e', '--entity', '--entity-address', metavar='ADDRESS', required=True,
                help='address of the agent where the jobs are installed.')
        self.parser.add_argument(
                '-j', '--job', type=str, default=None,
                help='job to add and install (if argument not specified, all jobs are installed)')
        self.parser.add_argument(
                '-u', '--user', default=getpass.getuser(),
                help='user to log into agent during the installation proccess')
        self.parser.add_argument(
                '-p', '--passwd', '--agent-password',
                dest='agent_password', nargs='?', const=self.PASSWORD_SENTINEL,
                help='password to log into agent during the installation process. '
                'use the flag but omit the value to get it asked using an echoless prompt; '
                'omit the flag entirelly to rely on SSH keys on the controller instead.')
        self.parser.add_argument(
                '-o', '--openbach-path', default="../../openbach/src/jobs",
                help='Path of jobs folder in OpenBACH repository')

    def parse(self, argv=None):
        args = super().parse(argv)
        if args.agent_password is self.PASSWORD_SENTINEL:
            prompt = 'Password for user {} on agents: '.format(args.user)
            self.args.agent_password = getpass.getpass(prompt)

    def execute(self, show_response_content=True):
        raise NotImplementedError


class DummyResponse:
    def __getitem__(self, key):
        logger = logging.getLogger(__name__)
        logger.debug('Trying to get the {} key from a bad response'.format(key))
        return self

    def __str__(self):
        logger = logging.getLogger(__name__)
        logger.warning('Using a bad response from an earlier call, request may fail from unexpected argument')
        return super().__str__()


def setup_logging(
        default_path='logging.json',
        default_level=logging.INFO,
        env_path_key='LOG_CFG',
        env_lvl_key='LOG_LVL',
):
    def basic_config(level=default_level):
        logging.basicConfig(
                level=level,
                format='[%(levelname)s][%(name)s:%(lineno)d:%(funcName)s]'
                       '[%(asctime)s.%(msecs)d]:%(message)s',
                datefmt='%Y-%m-%d:%H:%M:%S',
        )

    warnings = []
    level = os.getenv(env_lvl_key, None)
    if level:
        try:
            basic_config(level=level.upper())
        except (TypeError, ValueError) as e:
            warnings.append(
                    'Error when using the environment variable '
                    '{}: {}. Skipping.'.format(env_lvl_key, e))
        else:
            return

    path = default_path
    environ_path = os.getenv(env_path_key, None)
    if environ_path:
        path = environ_path

    try:
        config_file = open(path, 'rt')
    except FileNotFoundError:
        basic_config()
    else:
        with config_file:
            try:
                logging.config.fileConfig(config_file)
            except Exception:
                config_file.seek(0)
                try:
                    config = json.load(config_file)
                except json.JSONDecodeError:
                    warnings.append(
                            'File {} is neither in INI nor in JSON format, '
                            'using default level instead'.format(path))
                    basic_config()
                else:
                    try:
                        logging.config.dictConfig(config)
                    except Exception:
                        warnings.append(
                                'JSON file {} is not suitable for '
                                'a logging configuration, using '
                                'default level instead'.format(path))
                        basic_config()
    finally:
        logger = logging.getLogger(__name__)
        for warning in warnings:
            logger.warning(warning)


def _verify_response(response):
    logger = logging.getLogger(__name__)
    try:
        response.raise_for_status()
    except:
        logger.error('Something went wrong', exc_info=True)
        return DummyResponse()
    else:
        logger.info('Done')
        try:
            return response.json()
        except (AttributeError, json.JSONDecodeError):
            return DummyResponse()


def execute(openbach_function):
    logger = logging.getLogger(__name__)
    logger.info(
            'Starting OpenBACH function %s',
            openbach_function.__class__.__name__)

    openbach_function_args = vars(openbach_function.args)
    if openbach_function_args:
        logger.debug('Arguments used:')
        for name, value in openbach_function_args.items():
            logger.debug('\t%s: %s', name, '*****' if name == 'password' else value)

    try:
        response = openbach_function.execute(False)
    except ActionFailedError:
        logger.critical('Something went wrong', exc_info=True)
        return DummyResponse()

    if isinstance(response, list):
        return [_verify_response(r) for r in response]
    else:
        return _verify_response(response)


def main(argv=None):
    logger = logging.getLogger(__name__)
    logger.debug('TODO: detach and reatach agents')

    # Parse arguments
    validator = ValidationSuite()
    validator.parse(argv)

    controller = validator.credentials['controller']
    del validator.args.controller
    entity = validator.args.entity
    del validator.args.entity
    job = validator.args.job
    del validator.args.job
    install_user = validator.args.user
    del validator.args.user
    install_password = validator.args.agent_password
    del validator.args.agent_password
    openbach_path = validator.args.openbach_path
    del validator.args.openbach_path

    # List projects
    projects = validator.share_state(ListProjects)
    response = execute(projects)

    # Remove Projects
    project_names = {p['name'] for p in response}
    for project_name in project_names:
        remove_project = validator.share_state(DeleteProject)
        remove_project.args.project_name = project_name
        execute(remove_project)

    # Create project
    project_name = 'validation_suite_test_jobs'
    add_project = validator.share_state(CreateProject)
    add_project.args.project = {
            'name': project_name,
            'description': 'Test project for the Validation Suite',
            'owners': [],
    }
    execute(add_project)

    # Check created project
    project = validator.share_state(GetProject)
    project.args.project_name = project_name
    response = execute(project)

    # List agents
    agents = validator.share_state(ListAgents)
    agents.args.update = True
    agents.args.services = True
    response = execute(agents)

    # Detach all agents
    uninstall = validator.share_state(UninstallAgent)
    uninstall.args.detach = False
    for agent in response:
        if agent["project"] is not None:
            uninstall.args.agent_address = agent["address"]
            execute(uninstall)

    # Find agents unnatached to a project (must be all)
    free_agents = {
            agent['address']: {'name': agent['name'], 'collector': agent['collector_ip']}
            for agent in response
            if not agent['project'] and not agent['reserved'] and agent['address'] != controller
    }
    existing_names = {agent['name'] for agent in response}

    # List installed agents
    installed_agents = {}

    install_agent = validator.share_state(InstallAgent)
    install_agent.args.reattach = False
    install_agent.args.user = install_user
    install_agent.args.password = install_password
    for address, agent in free_agents.items():
        install_agent.args.agent_address = address
        install_agent.args.collector_address = agent['collector']
        install_agent.args.agent_name = agent['name']
        installed_agents[address] = agent['name']

    # Check if entity is in installed agents
    entities = {}
    if entity in installed_agents:
        entities[entity] = "entity"
    else:
        logger.error('Agent ' + agent + ' is not installed', exc_info=True)
        return DummyResponse()

    # Add Entities, associate agents
    add_entity = validator.share_state(AddEntity)
    add_entity.args.project_name = project_name
    add_entity.args.description = ''
    for agent_address, agent_name in entities.items():
        add_entity.args.entity_name = agent_name
        add_entity.args.agent_address = agent_address
        execute(add_entity)

    # List jobs in controller
    jobs = validator.share_state(ListJobs)
    jobs.args.string_to_search = None
    jobs.args.match_ratio = None
    response = execute(jobs)
    installed_jobs = {j['general']['name'] for j in response}

    # Delete all jobs on controller
    remove_job = validator.share_state(DeleteJob)
    for job_name in installed_jobs:
        remove_job.args.job_name = job_name
        execute(remove_job)

    # Get all available jobs path
    jobs_list = {}
    stable_jobs = Path(CWD.parent, 'externals_jobs', 'stable_jobs')
    for j in stable_jobs.glob('**/install_*.yml'):
        job_name = j.stem[len('install_'):]
        yaml_file = '{}.yml'.format(job_name)
        has_uninstall = j.with_name('uninstall_' + yaml_file).exists()
        has_description = Path(j.parent, 'files', yaml_file).exists()
        if has_uninstall and has_description:
            jobs_list[job_name] = j.parent.as_posix()
    stable_jobs = Path(CWD, openbach_path).resolve()
    for j in stable_jobs.glob('**/install_*.yml'):
        job_name = j.stem[len('install_'):]
        yaml_file = '{}.yml'.format(job_name)
        has_uninstall = j.with_name('uninstall_' + yaml_file).exists()
        has_description = Path(j.parent, 'files', yaml_file).exists()
        if has_uninstall and has_description:
            jobs_list[job_name] = j.parent.as_posix()

    # Get required jobs
    if job is not None:
        jobs = {}
        if job not in jobs_list:
            logger.error("Job " + job + " not found in openbach nor openbach-extra", exc_info=True)
            return DummyResponse()
        else:
            jobs[job] = jobs_list[job]
        jobs_list = jobs

    # Add and install jobs
    for job_name, job_path in jobs_list.items():
        add_job = validator.share_state(AddJob)
        add_job.args.path = None
        add_job.args.tarball = None
        add_job.args.files = job_path
        add_job.args.job_name = job_name
        r = execute(add_job)

        install_jobs = validator.share_state(InstallJobs)
        install_jobs.args.launch = False
        install_jobs.args.job_name = [[job_name]]
        install_jobs.args.agent_address = [[entity]]
        execute(install_jobs)

    nb_jobs = len(jobs_list)
    print(nb_jobs, "job(s) were to be installed")

    # List jobs added to controlled
    jobs = validator.share_state(ListJobs)
    jobs.args.string_to_search = None
    jobs.args.match_ratio = None
    response = execute(jobs)
    added_jobs = [j['general']['name'] for j in response]
    nb_jobs_added = len(added_jobs)
    print(nb_jobs_added, "job(s) have been added to controlled")

    # List jobs installed on agent
    installed_jobs = validator.share_state(ListInstalledJobs)
    installed_jobs.args.update = True
    installed_jobs.args.agent_address = entity
    response = execute(installed_jobs)
    installed_jobs = [job['name'] for job in response['installed_jobs']]
    nb_jobs_installed = len(installed_jobs)
    print(nb_jobs_installed, "job(s) have been installed on agent")

    if nb_jobs_added != nb_jobs:
        print("Not added jobs")
        for j in jobs_list.keys():
            if j not in added_jobs:
                print("   ", j)
        print()

    if nb_jobs_installed != nb_jobs:
        print("Not installed jobs")
        for j in jobs_list.keys():
            if j not in installed_jobs:
                print("   ", j)
        print()

if __name__ == '__main__':
    setup_logging()
    main(sys.argv[1:])
