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
'''

import os
import sys
import time
import getpass
import logging
import tempfile
import logging.config
from pathlib import Path
from contextlib import contextmanager
from argparse import FileType, Namespace

from requests.compat import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'apis'))

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


class InstallerBase(FrontendBase):
    PASSWORD_SENTINEL = object()

    def __init__(self):
        super().__init__('OpenBACH − Validation Suite')
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
                '--private-key-file', type=FileType('r'),
                help='path of private key file on the current computer to be sent to the controller')
        self.parser.add_argument(
                '--public-key-file', type=FileType('r'),
                help='path of public key file on the current computer to be sent to the controller')
        self.parser.add_argument(
                 '--http-proxy',
                help='http proxy variable for agents during the installation process')
        self.parser.add_argument(
                '--https-proxy',
                help='https proxy variable for agents during the installation process')

    def parse(self, argv=None):
        args = super().parse(argv)
        if args.agent_password is self.PASSWORD_SENTINEL:
            prompt = 'Password for user {} on agents: '.format(args.user)
            self.args.agent_password = getpass.getpass(prompt)

        public_key_filename = private_key_filename = None
        if args.public_key_file:
            with args.public_key_file:
                public_key_filename = args.public_key_file.name
        if args.private_key_file:
            with args.private_key_file:
                private_key_filename = args.private_key_file.name
        self.suite_args = Namespace(
                install_user = args.user,
                install_password = args.agent_password,
                http_proxy = args.http_proxy,
                https_proxy = args.https_proxy,
                private_key_file = private_key_filename,
                public_key_file = public_key_filename,
        )

        del args.user
        del args.agent_password
        del args.http_proxy
        del args.https_proxy
        del args.private_key_file
        del args.public_key_file

        return args

    def execute(self, show_response_content=True):
        raise NotImplementedError


class ValidationSuiteBase(InstallerBase):
    def __init__(self):
        super().__init__()
        self.parser.add_argument(
                '-s', '--server', '--server-address', metavar='ADDRESS', required=True,
                help='address of an agent acting as server for the reference scenarios; '
                'this can be an existing agent or a new machine to be installed.')
        self.parser.add_argument(
                '-S', '--server-ip', metavar='ADDRESS',
                help='private address of the server, for sockets to listen on; in case '
                'it is different from its public install address.')
        self.parser.add_argument(
                '-c', '--client', '--client-address', metavar='ADDRESS', required=True,
                help='address of an agent acting as client for the reference scenarios; '
                'this can be an existing agent or a new machine to be installed.')
        self.parser.add_argument(
                '-C', '--client-ip', metavar='ADDRESS',
                help='private address of the client, for sockets to send from; in case '
                'it is different from its public install address.')
        self.parser.add_argument(
                '-m', '--middlebox', '--middlebox-address', metavar='ADDRESS', required=True,
                help='address of an agent acting as middlebox for the reference scenarios; '
                'this can be an existing agent or a new machine to be installed.')
        middlebox_ip_group = self.parser.add_mutually_exclusive_group(required=True)
        middlebox_ip_group.add_argument(
                '-M', '--middlebox-ip', metavar='ADDRESS',
                help='private address of the middlebox, for routes management; in case '
                'it is different from its public install address.')
        middlebox_ip_group.add_argument(
                '-R', '--middlebox-route', nargs=2, metavar=('SERVER', 'CLIENT'),
                help='private addresses of the middlebox, for routes management; in case '
                'the client and the server reside on two different networks.')
        self.parser.add_argument(
                '-i', '--interfaces', '--middlebox-interfaces', required=True,
                help='comma-separated list of the network interfaces to emulate link on the middlebox')

    def parse(self, argv=None):
        args = super().parse(argv)

        middlebox_ip_server = middlebox_ip_client = args.middlebox_ip or args.middlebox
        if args.middlebox_route is not None:
            middlebox_ip_server, middlebox_ip_client = args.middlebox_route
        self.suite_args.client = args.client
        self.suite_args.client_ip = args.client_ip or args.client
        self.suite_args.server = args.server
        self.suite_args.server_ip = args.server_ip or args.server
        self.suite_args.middlebox = args.middlebox
        self.suite_args.middlebox_ip_server = middlebox_ip_server
        self.suite_args.middlebox_ip_client = middlebox_ip_client
        self.suite_args.middlebox_interfaces = args.interfaces

        del args.client
        del args.client_ip
        del args.server
        del args.server_ip
        del args.middlebox
        del args.middlebox_ip
        del args.middlebox_route
        del args.interfaces

        return args


class DummyResponse:
    def __getitem__(self, key):
        logger = logging.getLogger(__name__)
        logger.debug('Trying to get the {} key from a bad response'.format(key))
        return self

    def __str__(self):
        logger = logging.getLogger(__name__)
        logger.warning('Using a bad response from an earlier call, request may fail from unexpected argument')
        return super().__str__()


@contextmanager
def MaybeNotFile(filename, *args, **kwargs):
    logger = logging.getLogger(__name__)
    logger.debug('Trying to open the file: {}'.format(filename))
    if filename is None:
        yield
    else:
        with open(filename, *args, **kwargs) as f:
            logger.debug('Got the following handle: {} ({})'.format(repr(f), id(f)))
            yield f


def load_executor_from_path(path):
    import importlib
    import functools
    path = Path(path).resolve()
    module_name = path.stem.replace('-', '_')
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    executor = module.main

    @functools.wraps(executor)
    def wrapper(argv=None):
        try:
            return executor(argv)
        except SystemExit:
            pass

    return wrapper


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
            if name == 'use_controller_file':
                value = bool(value)
            elif 'password' in name:
                value = '*****'
            logger.debug('\t%s: %s', name, value)

    try:
        response = openbach_function.execute(False)
    except ActionFailedError:
        logger.critical('Something went wrong', exc_info=True)
        return DummyResponse()

    if isinstance(response, list):
        return [_verify_response(r) for r in response]
    else:
        return _verify_response(response)


def pick_unique_name(existing_names, prefix='ValidationSuite'):
    index = 0
    while (index := index + 1):
        name = f'{prefix}{index}'
        if name not in existing_names:
            existing_names.add(name)
            return name


def validation_list_collectors(validator):
    collectors = validator.share_state(ListCollectors)
    return execute(collectors)


def validation_install_collector(validator, address, name):
    install_collector = validator.share_state(AddCollector)
    install_collector.args.collector_address = address
    install_collector.args.agent_name = name
    install_collector.args.logs_port = 10514
    install_collector.args.stats_port = 2222
    install_collector.args.user = validator.suite_args.install_user
    install_collector.args.agent_password = validator.suite_args.install_password
    return execute(install_collector)


def validation_change_collector(validator, address, collector):
    change_collector = validator.share_state(AssignCollector)
    change_collector.args.agent_address = address
    change_collector.args.collector_address = collector
    return execute(change_collector)


def validation_remove_collector(validator, address):
    remove_collector = validator.share_state(DeleteCollector)
    remove_collector.args.collector_address = address
    return execute(remove_collector)


def validation_install_agents(validator, agents):
    install_agent = validator.share_state(InstallAgent)
    install_agent.args.reattach = False
    install_agent.args.user = validator.suite_args.install_user
    install_agent.args.password = validator.suite_args.install_password
    install_agent.args.http_proxy = validator.suite_args.http_proxy
    install_agent.args.https_proxy = validator.suite_args.https_proxy
    public_key_file = validator.suite_args.public_key_file
    private_key_file = validator.suite_args.private_key_file
    for address, agent in agents.items():
        with MaybeNotFile(private_key_file) as private_key, MaybeNotFile(public_key_file) as public_key:
            install_agent.args.private_key_file = private_key
            install_agent.args.public_key_file = public_key
            install_agent.args.agent_address = address
            install_agent.args.collector_address = agent['collector']
            install_agent.args.agent_name = agent['name']
            execute(install_agent)


def validation_list_agents(validator, refresh=True):
    agents = validator.share_state(ListAgents)
    agents.args.update = refresh
    agents.args.services = refresh
    return execute(agents)


def validation_uninstall_agents(validator, agents):
    uninstall = validator.share_state(UninstallAgent)
    uninstall.args.detach = False
    for address in agents:
        uninstall.args.agent_address = address
        execute(uninstall)


def validation_list_projects(validator):
    projects = validator.share_state(ListProjects)
    return execute(projects)


def validation_create_project(validator, project_name):
    add_project = validator.share_state(CreateProject)
    add_project.args.project = {
            'name': project_name,
            'description': 'Test project for the Validation Suite',
            'owners': [],
    }
    return execute(add_project)


def validation_get_project(validator, project_name):
    project = validator.share_state(GetProject)
    project.args.project_name = project_name
    return execute(project)


def validation_modify_project(validator, project_name, project_content):
    modify_project = validator.share_state(ModifyProject)
    modify_project.args.project = project_content
    modify_project.args.project_name = project_name
    return execute(modify_project)


def validation_remove_project(validator, project_name):
    remove_project = validator.share_state(DeleteProject)
    remove_project.args.project_name = project_name
    return execute(remove_project)


def validation_add_project(validator, project_content):
    with tempfile.NamedTemporaryFile('w') as project_file:
        json.dump(project_content, project_file)
        project_file.flush()
        add_project_parser = AddProject()
        add_project_parser.parse([project_file.name, '--controller', 'localhost', '--ignore-controller-file'])
    add_project = validator.share_state(AddProject)  # allows to reuse connection cookie
    add_project.args.project = add_project_parser.args.project
    return execute(add_project)


def validation_add_entity(validator, project_name, agents=None, prefix='Entity'):
    add_entity = validator.share_state(AddEntity)
    add_entity.args.project_name = project_name
    add_entity.args.description = ''
    if agents is None or isinstance(agents, str):
        add_entity.args.entity_name = prefix
        add_entity.args.agent_address = agents
        return execute(add_entity)
    else:
        for i, agent_address in enumerate(agents):
            add_entity.args.entity_name = f'{prefix}{i}'
            add_entity.args.agent_address = agent_address
            execute(add_entity)


def validation_list_entities(validator, project_name):
    response = validation_get_project(validator, project_name)
    return response['entity']


def validation_remove_entities(validator, project_name, entities):
    remove_entity = validator.share_state(DeleteEntity)
    remove_entity.args.project_name = project_name
    for entity in entities:
        remove_entity.args.entity_name = entity['name']
        execute(remove_entity)


def validation_list_installed_jobs(validator, agents):
    installed_jobs = validator.share_state(ListInstalledJobs)
    installed_jobs.args.update = True
    for address in agents:
        installed_jobs.args.agent_address = address
        response = execute(installed_jobs)
        yield address, [job['name'] for job in response['installed_jobs']]


def validation_list_jobs(validator):
    jobs = validator.share_state(ListJobs)
    jobs.args.string_to_search = None
    jobs.args.match_ratio = None
    return execute(jobs)


def validation_add_jobs(validator, jobs):
    add_job = validator.share_state(AddJob)
    add_job.args.path = None
    add_job.args.tarball = None
    for job_name, job_path in jobs.items():
        add_job.args.files = job_path
        add_job.args.job_name = job_name
        execute(add_job)


def validation_install_jobs(validator, jobs_names, agents_addresses):
    install_jobs = validator.share_state(InstallJobs)
    install_jobs.args.launch = False
    install_jobs.args.job_name = jobs_names
    install_jobs.args.agent_address = agents_addresses
    return execute(install_jobs)


def validation_state_job(validator, job_name, agent_address):
    state_job = validator.share_state(StateJob)
    state_job.args.job_name = job_name
    state_job.args.agent_address = agent_address
    return execute(state_job)


def validation_uninstall_jobs(validator, jobs_names, agents_addresses):
    uninstall_jobs = validator.share_state(UninstallJobs)
    uninstall_jobs.args.launch = False
    uninstall_jobs.args.job_name = jobs_names
    uninstall_jobs.args.agent_address = agents_addresses
    return execute(uninstall_jobs)


def validation_remove_jobs(validator, jobs):
    remove_job = validator.share_state(DeleteJob)
    for job_name in jobs:
        remove_job.args.job_name = job_name
        execute(remove_job)


def validation_start_job_instance(validator, job_name, agent_address, arguments=None):
    start_job = validator.share_state(StartJobInstance)
    start_job.args.job_name = job_name
    start_job.args.argument = {} if arguments is None else arguments
    start_job.args.interval = None
    start_job.args.agent_address = agent_address
    return execute(start_job)


def validation_list_job_instances(validator, agent_address):
    job_instances = validator.share_state(ListJobInstances)
    job_instances.args.agent_address = [agent_address]
    job_instances.args.update = True
    return execute(job_instances)


def validation_stop_job_instances(validator, job_instance_ids):
    stop_job = validator.share_state(StopJobInstance)
    stop_job.args.job_instance_id = job_instance_ids
    return execute(stop_job)


def validation_stop_job_instance(validator, job_instance_id):
    return validation_stop_job_instances(validator, [job_instance_id])


def validation_status_job_instance_stops(validator, job_instance_id):
    status_job = validator.share_state(StatusJobInstance)
    status_job.args.update = True
    status_job.args.job_instance_id = job_instance_id
    while True:
        time.sleep(1)
        response = execute(status_job)
        if response['status'] != 'Running':
            return response


def validation_stop_all_job_instances(validator, agent_address):
    stop_job = validator.share_state(StopAllJobInstances)
    stop_job.args.agent_address = [agent_address]
    stop_job.args.job_name = []
    return execute(stop_job)


def validation_add_scenario(validator, project_name, scenario_content):
    add_scenario = validator.share_state(CreateScenario)
    add_scenario.args.project_name = project_name
    add_scenario.args.scenario = scenario_content
    return execute(add_scenario)


def validation_add_scenario_from_file(validator, project_name, filename):
    scenario_parser = AddScenario()
    scenario_parser.parse([filename, project_name, '--controller', 'localhost', '--ignore-controller-file'])
    return validation_add_scenario(validator, project_name, scenario_parser.args.scenario)


def validation_modify_scenario(validator, project_name, scenario_name, scenario_content):
    modify_scenario = validator.share_state(ModifyScenario)
    modify_scenario.args.scenario_name = scenario_name
    modify_scenario.args.project_name = project_name
    modify_scenario.args.scenario = scenario_content
    return execute(modify_scenario)


def validation_modify_scenario_from_file(validator, project_name, scenario_name, filename):
    scenario_parser = ModifyScenario()
    scenario_parser.parse([scenario_name, project_name, filename, '--controller', 'localhost', '--ignore-controller-file'])
    return validation_modify_scenario(validator, project_name, scenario_name, scenario_parser.args.scenario)


def validation_remove_scenario(validator, project_name, scenario_name):
    remove_scenario = validator.share_state(DeleteScenario)
    remove_scenario.args.project_name = project_name
    remove_scenario.args.scenario_name = scenario_name
    return execute(remove_scenario)


def validation_start_scenario(validator, project_name, scenario_name, arguments=None):
    start_scenario = validator.share_state(StartScenarioInstance)
    start_scenario.args.project_name = project_name
    start_scenario.args.scenario_name = scenario_name
    start_scenario.args.argument = {} if arguments is None else arguments
    response = execute(start_scenario)
    return response['scenario_instance_id']


def validation_stop_scenario(validator, scenario_id):
    stop_scenario = validator.share_state(StopScenarioInstance)
    stop_scenario.args.scenario_instance_id = scenario_id
    return execute(stop_scenario)


def validation_status_scenario_stops(validator, scenario_id):
    status_scenario = validator.share_state(StatusScenarioInstance)
    status_scenario.args.scenario_instance_id = scenario_id
    while True:
        time.sleep(1)
        response = execute(status_scenario)
        if response['status'] != 'Running':
            return response


def validation_get_scenario_instance_data(validator, scenario_id, folder):
    scenario_data = validator.share_state(GetScenarioInstanceData)
    scenario_data.args.file = []
    scenario_data.args.scenario_instance_id = scenario_id
    scenario_data.args.path = folder
    return execute(scenario_data)
