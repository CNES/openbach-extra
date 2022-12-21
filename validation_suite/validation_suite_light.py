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
        self.parser.add_argument(
                '-M', '--middlebox-ip', metavar='ADDRESS',
                help='private address of the middlebox, for routes management; in case '
                'it is different from its public install address.')
        self.parser.add_argument(
                '-e', '--agent', '--extra-agent', metavar='ADDRESS', action='append', default=[],
                help='address of an extra agent to install during the tests; can be specified '
                'several times.')
        self.parser.add_argument(
                '-i', '--interfaces', '--middlebox-interfaces', required=True,
                help='comma-separated list of the network interfaces to emulate link on the middlebox')
        self.parser.add_argument(
                '-k', '--keep-installed-jobs', action='store_true',
                help='If enabled, jobs with are kept on agents. Jobs are installed only if not on agent. '
                'Otherwise, remove installed jobs from controller and reinstall only needed.')
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


def load_executor_from_path(path):
    import importlib
    import functools
    path = Path(path).resolve()
    module_name = path.stem.replace('-', '_')
    spec = importlib.util.spec_from_file_location(module_name, path.as_posix())
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
    new_agents = validator.args.agent
    del validator.args.agent
    client = validator.args.client
    del validator.args.client
    client_ip = validator.args.client_ip or client
    del validator.args.client_ip
    server = validator.args.server
    del validator.args.server
    server_ip = validator.args.server_ip or server
    del validator.args.server_ip
    middlebox = validator.args.middlebox
    del validator.args.middlebox
    middlebox_ip = validator.args.middlebox_ip or middlebox
    del validator.args.middlebox_ip
    middlebox_interfaces = validator.args.interfaces
    del validator.args.interfaces
    keep_installed_jobs = validator.args.keep_installed_jobs
    del validator.args.keep_installed_jobs
    install_user = validator.args.user
    del validator.args.user
    install_password = validator.args.agent_password
    del validator.args.agent_password
    openbach_path = validator.args.openbach_path
    del validator.args.openbach_path

    required_jobs = {}
    required_jobs["default_admin"] = {"server": ["send_logs", "send_stats", "synchronization"],
                                      "middlebox": ["send_logs", "send_stats", "synchronization"],
                                      "client": ["send_logs", "send_stats", "synchronization"]}
    """
    required_jobs["default_admin"] = {"server": ["send_logs", "kernel_compile", "send_stats", "synchronization"],
                                      "middlebox": ["send_logs", "kernel_compile", "send_stats", "synchronization"],
                                      "client": ["send_logs", "kernel_compile", "send_stats", "synchronization"]}
    """
    required_jobs["default_post_processing"] = {"server": ["temporal_binning_statistics", "temporal_binning_histogram", "histogram", "comparison", "pcap_postprocessing", "time_series"],
                                                "middlebox": ["temporal_binning_statistics", "temporal_binning_histogram", "histogram", "comparison", "pcap_postprocessing", "time_series"],
                                                "client": ["temporal_binning_statistics", "temporal_binning_histogram", "histogram", "comparison", "pcap_postprocessing", "time_series"]}

    required_jobs["tests_json"] = {"server": ["ip_route", "fping"],
                                      "middlebox": ["ip_route"],
                                      "client": ["ip_route"]}

    required_jobs["data_transfer_configure_link"] = {"server": ["iperf3"],
                                                     "middlebox": ["tc_configure_link"],
                                                     "client": ["iperf3"]}

    required_jobs["network_delay"] = {"server": ["d-itg_recv", "synchronization"],
                                      "middlebox": ["time_series", "histogram"],
                                      "client": ["fping", "d-itg_send", "synchronization"]}
    required_jobs["network_jitter"] = {"server": ["owamp-server", "synchronization"],
                                       "middlebox": ["time_series", "histogram"],
                                       "client": ["owamp-client", "synchronization"]}
    required_jobs["network_rate"] = {"server": ["iperf3", "nuttcp", "synchronization"],
                                     "middlebox": ["time_series", "histogram"],
                                     "client": ["iperf3", "nuttcp", "synchronization"]}
    required_jobs["network_owd"] = {"server": ["d-itg_recv", "owamp-server", "synchronization"],
                                    "middlebox": ["time_series", "histogram"],
                                    "client": ["d-itg_send", "owamp-client", "synchronization"]}
    required_jobs["network_global"] = {"server": ["iperf3", "nuttcp", "d-itg_recv", "owamp-server", "synchronization"],
                                       "middlebox": ["time_series", "histogram"],
                                       "client": ["iperf3", "nuttcp", "fping", "d-itg_send", "owamp-client", "synchronization"]}

    required_jobs["service_ftp"] = {"server": ["ftp_srv"],
                                    "middlebox": ["time_series", "histogram"],
                                    "client": ["ftp_clt"]}
    required_jobs["service_dash"] = {"server": ["apache2"],
                                     "middlebox": ["time_series", "histogram"],
                                     "client": ["dashjs_client"]}
    required_jobs["service_voip"] = {"server": ["voip_qoe_dest"],
                                     "middlebox": ["time_series", "histogram"],
                                     "client": ["voip_qoe_src"]}
    required_jobs["service_web"] = {"server": ["apache2"],
                                    "middlebox": ["time_series", "histogram"],
                                    "client": ["web_browsing_qoe"]}

    required_jobs["transport_oneflow"] = {"server": ["iperf3"],
                                          "middlebox": ["time_series", "histogram"],
                                          "client": ["iperf3"]}

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
    project_name = 'validation_suite_light'
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
    
    # Modify project
    response['description'] = textwrap.dedent("""
        Test project for the Validation Suite

        Will use temporary entities to link to unused
        agents as well as extra agents provided for
        the purpose of the validation suite.
    """)
    modify_project = validator.share_state(ModifyProject)
    modify_project.args.project = response
    modify_project.args.project_name = project_name
    execute(modify_project)

    # Remove Project
    remove_project = validator.share_state(DeleteProject)
    remove_project.args.project_name = project_name
    execute(remove_project)

    # Add project from file
    with tempfile.NamedTemporaryFile('w') as project_file:
        json.dump(response, project_file)
        project_file.flush()
        add_project_parser = AddProject()
        add_project_parser.parse([project_file.name, '--controller', controller])
    add_project = validator.share_state(AddProject)  # allows to reuse connection cookie
    add_project.args.project = add_project_parser.args.project
    del add_project_parser
    execute(add_project)

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

    # Check if server, middlebox and clients in installed agents
    entities = {}
    for agent in ("client", "server", "middlebox"):
        if eval(agent) in installed_agents:
            entities[eval(agent)] = agent
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
    installed_jobs = {job['general']['name'] for job in response}

    # Delete all jobs on controller
    if not keep_installed_jobs:
        remove_job = validator.share_state(DeleteJob)
        for job_name in installed_jobs:
            remove_job.args.job_name = job_name
            execute(remove_job)

    # Get all available jobs path
    jobs_list = {}
    stable_jobs = Path(CWD.parent, 'externals_jobs', 'stable_jobs')
    for job in stable_jobs.glob('**/install_*.yml'):
        job_name = job.stem[len('install_'):]
        yaml_file = '{}.yml'.format(job_name)
        has_uninstall = job.with_name('uninstall_' + yaml_file).exists()
        has_description = Path(job.parent, 'files', yaml_file).exists()
        if has_uninstall and has_description:
            jobs_list[job_name] = job.parent.as_posix()
    stable_jobs = Path(CWD, openbach_path).resolve()
    for job in stable_jobs.glob('**/install_*.yml'):
        job_name = job.stem[len('install_'):]
        yaml_file = '{}.yml'.format(job_name)
        has_uninstall = job.with_name('uninstall_' + yaml_file).exists()
        has_description = Path(job.parent, 'files', yaml_file).exists()
        if has_uninstall and has_description:
            jobs_list[job_name] = job.parent.as_posix()

    # Add required jobs
    jobs = {}
    for scenario in required_jobs.values():
        for js in scenario.values():
            for j in js:
                if j not in jobs_list:
                    logger.error("Job " + j + " not found in openbach nor openbach-extra", exc_info=True)
                jobs[j] = jobs_list[j]
    add_job = validator.share_state(AddJob)
    add_job.args.path = None
    add_job.args.tarball = None
    for job_name, job_path in jobs.items():
        add_job.args.files = job_path
        add_job.args.job_name = job_name
        execute(add_job)

    jobs_per_agent = {}
    # List jobs installed on each agent
    for address, agent in entities.items():
        installed_jobs = validator.share_state(ListInstalledJobs)
        installed_jobs.args.update = True
        installed_jobs.args.agent_address = address
        response = execute(installed_jobs)
        installed_jobs = [job['name'] for job in response['installed_jobs']]
        jobs_per_agent[agent] = [job['name'] for job in response['installed_jobs']]

    # Install on agents
    total_names = []
    total_addresses = []
    for address, agent in entities.items():
        job_names = set()
        for scenario in required_jobs.values():
            job_names.update(scenario[agent])
        job_names_updated = []
        for job_name in list(job_names):
            if job_name not in jobs_per_agent[agent]:
                job_names_updated.append(job_name)
        total_names.append(list(job_names))
        total_addresses.append([address])
    install_jobs = validator.share_state(InstallJobs)
    install_jobs.args.launch = False
    install_jobs.args.job_name = total_names
    install_jobs.args.agent_address = total_addresses
    execute(install_jobs)

    # Create scenario
    with CWD.joinpath('scenario_stops_light.json').open() as f:
        scenario_name = json.load(f)['name']

    add_scenario = validator.share_state(CreateScenario)
    add_scenario.args.project_name = project_name
    add_scenario.args.scenario = {
            'name': scenario_name,
            'description': 'simple scenario that stops itself',
            'openbach_functions': [],
    }
    execute(add_scenario)

    # Modify scenario
    scenario_parser = ModifyScenario()
    scenario_parser.parse([
        scenario_name,
        project_name,
        CWD.joinpath('scenario_stops_light.json').as_posix(),
        '--controller', controller,
    ])
    modify_scenario = validator.share_state(ModifyScenario)  # allows to reuse connection cookie
    modify_scenario.args.scenario_name = scenario_name
    modify_scenario.args.project_name = project_name
    modify_scenario.args.scenario = scenario_parser.args.scenario
    execute(modify_scenario)

    # Add scenario from file (stops manually)
    scenario_parser = AddScenario()
    scenario_parser.parse([
        CWD.joinpath('scenario_runs_light.json').as_posix(),
        project_name,
        '--controller', controller,
    ])
    add_scenario = validator.share_state(AddScenario)  # allows to reuse connection cookie
    add_scenario.args.project_name = project_name
    add_scenario.args.scenario = scenario_parser.args.scenario
    del scenario_parser
    execute(add_scenario)

    # Run scenarios
    start_scenario = validator.share_state(StartScenarioInstance)
    start_scenario.args.project_name = project_name
    start_scenario.args.argument = {}

    start_scenario.args.scenario_name = scenario_name
    response = execute(start_scenario)
    stops_itself_id = response['scenario_instance_id']

    start_scenario.args.scenario_name = add_scenario.args.scenario['name']
    response = execute(start_scenario)
    should_be_stopped_id = response['scenario_instance_id']

    # Status scenario instances (until first stops)
    status_scenario = validator.share_state(StatusScenarioInstance)
    status_scenario.args.scenario_instance_id = stops_itself_id
    while True:
        time.sleep(1)
        response = execute(status_scenario)
        if response['status'] != 'Running':
            break

    # Stop scenario (second one)
    stop_scenario = validator.share_state(StopScenarioInstance)
    stop_scenario.args.scenario_instance_id = should_be_stopped_id
    execute(stop_scenario)

    status_scenario.args.scenario_instance_id = should_be_stopped_id
    while True:
        time.sleep(1)
        response = execute(status_scenario)
        if response['status'] != 'Running':
            break

    # Get scenario instance data
    scenario_data = validator.share_state(GetScenarioInstanceData)
    scenario_data.args.file = []
    scenario_data.args.scenario_instance_id = stops_itself_id
    with tempfile.TemporaryDirectory() as tempdir:
        scenario_data.args.path = Path(tempdir)
        execute(scenario_data)

    # Start job instance times X
    job_name = 'fping'
    instances_amount = 7  # Beware, not too high as the agent can't handle more than 10 tasks at once
    agent_address = {v:k for k,v in entities.items()}["server"]

    start_job = validator.share_state(StartJobInstance)
    start_job.args.job_name = job_name
    start_job.args.argument = {'destination_ip': '127.0.0.1'}
    start_job.args.interval = None
    start_job.args.agent_address = agent_address
    for _ in range(instances_amount):
        response = execute(start_job)
    watched_job = response['job_instance_id']

    # Check instances
    job_instances = validator.share_state(ListJobInstances)
    job_instances.args.agent_address = [agent_address]
    job_instances.args.update = True
    response = execute(job_instances)

    try:
        agent, = (a for a in response['instances'] if a['address'] == agent_address)
        job, = (j for j in agent['installed_jobs'] if j['job_name'] == job_name)
        instances = [i for i in job['instances'] if i['status'] == 'Running']
        if len(instances) != instances_amount:
            logger.warning(
                    'Expected %d running instances of %s but found %d instead', 
                    instances_amount, job_name, len(instances))
    except ValueError:
        logger.error('Error while getting number of instances of {}', job_name)

    # Stop one
    stop_job = validator.share_state(StopJobInstance)
    stop_job.args.job_instance_id = [watched_job]
    execute(stop_job)

    # Stop all
    stop_job = validator.share_state(StopAllJobInstances)
    stop_job.args.agent_address = [agent_address]
    stop_job.args.job_name = []
    execute(stop_job)

    # Status job instances
    status_job = validator.share_state(StatusJobInstance)
    status_job.args.update = True
    status_job.args.job_instance_id = watched_job
    while True:
        time.sleep(1)
        response = execute(status_job)
        if response['status'] != 'Running':
            break

    # Setup routes between client and server to use the middlebox
    start_job.args.job_name = 'ip_route'
    start_job.args.interval = None
    start_job.args.agent_address = server
    start_job.args.argument = {
            'operation': 'replace',
            'gateway_ip': middlebox_ip,
            'destination_ip': {'network_ip': '{}/32'.format(client_ip)}
    }
    execute(start_job)
    
    start_job.args.agent_address = client
    start_job.args.argument = {
            'operation': 'replace',
            'gateway_ip': middlebox_ip,
            'destination_ip': {'network_ip': '{}/32'.format(server_ip)}
    }
    execute(start_job)


    # Run example executors
    logger.info('Running example executors:')

    logger.info('  Data transfer configure link')
    data_transfer_path = Path(CWD.parent, 'executors', 'examples', 'data_transfer_configure_link.py')
    data_transfer_configure_link = load_executor_from_path(data_transfer_path)
    data_transfer_configure_link([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--entity', 'middlebox',
        '--server', 'server',
        '--client', 'client',
        '--file-size', '10M',
        '--bandwidth-server-to-client', '10M',
        '--bandwidth-client-to-server', '10M',
        '--delay-server-to-client', '10',
        '--delay-client-to-server', '10',
        '--client-ip', client_ip,
        '--middlebox-interfaces', middlebox_interfaces,
        project_name, 'run',
    ])

    # Run reference executors
    logger.info('Running reference executors:')
    executors_path = Path(CWD.parent, 'executors', 'references')

    logger.info('  Network Delay')
    network_delay = load_executor_from_path(executors_path.joinpath('executor_network_delay.py'))
    network_delay([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', server_ip,
        '--client-ip', client_ip,
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Network Jitter')
    network_jitter = load_executor_from_path(executors_path.joinpath('executor_network_jitter.py'))
    network_jitter([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', server_ip,
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Network Rate')
    network_rate = load_executor_from_path(executors_path.joinpath('executor_network_rate.py'))
    network_rate([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', server_ip,
        '--rate-limit', '10M',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    #~logger.info('  Network QOS')
    #~network_qos = load_executor_from_path(executors_path.joinpath('executor_network_qos.py'))
    #~network_qos([
    #~    '--controller', controller,
    #~    '--login', validator.credentials.get('login', ''),
    #~    '--password', validator.credentials.get('password', ''),
    #~    project_name, 'run',
    #~])

    logger.info('  Network One Way Delay')
    network_owd = load_executor_from_path(executors_path.joinpath('executor_network_one_way_delay.py'))
    network_owd([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', server_ip,
        '--client-ip', client_ip,
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Network Global')
    network_global = load_executor_from_path(executors_path.joinpath('executor_network_global.py'))
    network_global([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', server_ip,
        '--client-ip', client_ip,
        '--rate-limit', '10M',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Service FTP')
    service_ftp = load_executor_from_path(executors_path.joinpath('executor_service_ftp.py'))
    service_ftp([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', server_ip,
        '--mode', 'download',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Service Video Dash')
    service_dash = load_executor_from_path(executors_path.joinpath('executor_service_video_dash.py'))
    service_dash([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', server_ip,
        '--duration', '30',
        '--launch-server',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Service VoIP')
    service_voip = load_executor_from_path(executors_path.joinpath('executor_service_voip.py'))
    service_voip([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', server_ip,
        '--client-ip', client_ip,
        '--server-port', '8010',
        '--duration', '30',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Service Web Browsing')
    service_web = load_executor_from_path(executors_path.joinpath('executor_service_web_browsing.py'))
    service_web([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--duration', '30',
        '--url', 'https://{}:8081/website_openbach/www.openbach.org/content/home.php'.format(server_ip),
        '--url', 'https://{}:8082/website_cnes/cnes.fr/fr/index.html'.format(server_ip),
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    #logger.info('  Service Traffic Mix')
    #service_mix = load_executor_from_path(executors_path.joinpath('executor_service_traffic_mix.py'))
    #service_mix([
    #    '--controller', controller,
    #    '--login', validator.credentials.get('login', ''),
    #    '--password', validator.credentials.get('password', ''),
    #    '--data-transfer', '1', 'server', 'Client', '60', 'None', 'None', '0', server_ip, client_ip, '5201', '10M', '0', '1500',
    #    '--dash', '2', 'server', 'client', '60', 'None', 'None', '0', server_ip, client_ip, 'http/2', '5301',
    #    # To avoid proxy issues using config.yml, disable web-browsing
    #    # '--web-browsing', '3', 'server', 'client', '60', 'None', 'None', '0', server_ip, client_ip, '10', '2',
    #    '--voip', '4', 'server', 'client', '60', 'None', 'None', '0', server_ip, client_ip, '8011', 'G.711.1', '100.0', '120.0',
    #    '--data-transfer', '5', 'server', 'client', '60', '4', 'None', '5', server_ip, client_ip, '5201', '10M', '0', '1500',
    #    '--dash', '6', 'server', 'client', '60', '4', 'None', '5', server_ip, client_ip, 'http/2', '5301',
    #    # To avoid proxy issues using config.yml, disable web-browsing
    #    # '--web-browsing', '7', 'server', 'client', '60', '4', 'None', '5', server_ip, client_ip, '10', '2',
    #    '--voip', '8', 'server', 'client', '60', '4', 'None', '5', server_ip, client_ip, '8012', 'G.711.1', 'None', 'None',
    #    '--post-processing-entity', 'middlebox',
    #    project_name, 'run',
    #])

    logger.info('  Transport TCP One Flow')
    transport_oneflow = load_executor_from_path(executors_path.joinpath('executor_transport_tcp_one_flow.py'))
    transport_oneflow([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', server_ip,
        '--transmitted-size', '1G',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    #~logger.info('  Transport TCP Stack Conf')
    #~transport_stack = load_executor_from_path(executors_path.joinpath('executor_transport_tcp_stack_conf.py'))
    #~transport_stack([
    #~    '--controller', controller,
    #~    '--login', validator.credentials.get('login', ''),
    #~    '--password', validator.credentials.get('password', ''),
    #~    project_name, 'run',
    #~])

    # Remove routes between client and server to use the middlebox
    start_job.args.job_name = 'ip_route'
    start_job.args.interval = None
    start_job.args.agent_address = server
    start_job.args.argument = {
            'operation': 'delete',
            'destination_ip': {'network_ip': '{}/32'.format(client_ip)}
    }
    execute(start_job)
    start_job.args.agent_address = client
    start_job.args.argument = {
            'operation': 'delete',
            'destination_ip': {'network_ip': '{}/32'.format(server_ip)}
    }
    execute(start_job)


if __name__ == '__main__':
    setup_logging()
    main(sys.argv[1:])
