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

import sys
import time
import logging
import textwrap
import tempfile
import itertools
from pathlib import Path
from random import sample
from collections import Counter

from validation_suite_utils import (
        ValidationSuiteBase,
        json,
        setup_logging,
        pick_unique_name,
        load_executor_from_path,
        validation_list_collectors,
        validation_install_collector,
        validation_change_collector,
        validation_remove_collector,
        validation_install_agents,
        validation_list_agents,
        validation_uninstall_agents,
        validation_list_projects,
        validation_create_project,
        validation_get_project,
        validation_modify_project,
        validation_remove_project,
        validation_add_project,
        validation_add_entity,
        validation_list_entities,
        validation_remove_entities,
        validation_list_installed_jobs,
        validation_list_jobs,
        validation_add_jobs,
        validation_install_jobs,
        validation_state_job,
        validation_uninstall_jobs,
        validation_remove_jobs,
        validation_start_job_instance,
        validation_list_job_instances,
        validation_stop_job_instance,
        validation_status_job_instance_stops,
        validation_stop_all_job_instances,
        validation_add_scenario,
        validation_add_scenario_from_file,
        validation_modify_scenario_from_file,
        validation_remove_scenario,
        validation_start_scenario,
        validation_stop_scenario,
        validation_status_scenario_stops,
        validation_get_scenario_instance_data,
)


CWD = Path(__file__).resolve().parent


class ValidationSuite(ValidationSuiteBase):
    def __init__(self):
        super().__init__()
        self.parser.add_argument(
                '-e', '--agent', '--extra-agent', metavar='ADDRESS', action='append', default=[],
                help='address of an extra agent to install during the tests; can be specified '
                'several times.')
        self.parser.add_argument(
                '-w', '--whitelist', '--whitelist-jobs', nargs='+', default=[],
                help='installation will only try to install jobs randomly from this list if present')

    def parse(self, argv=None):
        args = super().parse(argv)
        self.suite_args.new_agents = args.agent
        self.suite_args.whitelist = set(args.whitelist)
        del args.agent
        del args.whitelist
        return args


def main(argv=None):
    logger = logging.getLogger(__name__)
    logger.debug('TODO: detach and reatach agents')

    # Parse arguments
    validator = ValidationSuite()
    validator.parse(argv)
    controller = validator.args.controller
    client = validator.suite_args.client
    server = validator.suite_args.server
    middlebox = validator.suite_args.middlebox

    # Find a unique project name for the rest of the tests
    response = validation_list_projects(validator)
    project_names = {p['name'] for p in response}
    project_name = pick_unique_name(project_names, 'Validation Suite ')

    # Find agents unnatached to a project and remember their installed jobs
    response = validation_list_agents(validator)
    free_agents = {
            agent['address']: {'name': agent['name'], 'collector': agent['collector_ip']}
            for agent in response
            if not agent['project'] and not agent['reserved'] and agent['address'] != controller
    }
    existing_names = {agent['name'] for agent in response}
    for address, jobs in validation_list_installed_jobs(validator, free_agents):
        free_agents[address]['jobs'] = jobs

    # Find a collector to use later
    validation_uninstall_agents(validator, free_agents)
    response = validation_list_collectors(validator)
    available_collectors = Counter(collector['address'] for collector in response)
    available_collectors.update(agent['collector'] for agent in free_agents.values())
    (selected_collector, _), = available_collectors.most_common(1)

    # Install agents (unnatached + command-line)
    validation_install_agents(validator, free_agents)
    installed_agents = {address: agent['name'] for address, agent in free_agents.items()}

    new_agents = {
            address: {'name': pick_unique_name(existing_names), 'collector': selected_collector}
            for address in validator.suite_args.new_agents
    }
    new_agents.update({
            agent: {'name': pick_unique_name(existing_names, prefix), 'collector': selected_collector}
            for agent, prefix in ((client, 'Client'), (server, 'Server'), (middlebox, 'MiddleBox'))
            if agent not in free_agents
    })
    validation_install_agents(validator, new_agents)
    installed_agents.update({address: agent['name'] for address, agent in new_agents.items()})

    # Find an agent without collector and validate collector-related functions
    collector_candidates = {
            agent
            for agent in installed_agents
            if agent not in available_collectors
    }
    if collector_candidates:
        installed_collector, *_ = collector_candidates
        installed_name = installed_agents[installed_collector]
        validation_install_collector(validator, installed_collector, installed_name)
        validation_change_collector(validator, installed_collector, selected_collector)
        logger.debug('TODO: Modify collector (How?)')
        validation_remove_collector(validator, installed_collector)
        try:
            previous_collector = free_agents[installed_collector]['collector']
        except KeyError:
            previous_collector = selected_collector
        reinstall_agent = {'name': installed_name, 'collector': previous_collector}
        validation_install_agents(validator, {installed_collector: reinstall_agent})

    logger.debug('TODO: Reserve an agent for the upcomming project')

    # Validate project-related functions
    validation_create_project(validator, project_name)
    response = validation_get_project(validator, project_name)
    response['description'] = textwrap.dedent("""
        Test project for the Validation Suite

        Will use temporary entities to link to unused
        agents as well as extra agents provided for
        the purpose of the validation suite.
    """)
    validation_modify_project(validator, project_name, response)
    validation_remove_project(validator, project_name)
    validation_add_project(validator, response)

    # Check free agents
    response = validation_list_agents(validator, refresh=False)
    available_agents = {
            agent['address']
            for agent in response
            if (not agent['project'] or agent['reserved'] == project_name) and agent['address'] != controller
    }
    if set(installed_agents) != available_agents:
        logger.warning(
                'Agents available for the project %s are different '
                'than the ones computed previously. Expected %s, got %s',
                project_name, set(installed_agents), available_agents)

    # Validate entity-related functions
    validation_add_entity(validator, project_name, installed_agents)
    validation_add_entity(validator, project_name, None, prefix='Naked Entity')
    entities = validation_list_entities(validator, project_name)
    validation_remove_entities(validator, project_name, entities)
    validation_add_entity(validator, project_name, client, prefix='Client')
    validation_add_entity(validator, project_name, middlebox, prefix='Middlebox')
    validation_add_entity(validator, project_name, server, prefix='Server')

    # Validate job-related functions
    response = validation_list_jobs(validator)
    installed_jobs = {job['general']['name'] for job in response}
    external_jobs = {}
    stable_jobs = CWD.parent / 'externals_jobs' / 'stable_jobs'
    for job in stable_jobs.glob('**/install_*.yml'):
        job_name = job.stem[len('install_'):]
        yaml_file = '{}.yml'.format(job_name)
        has_uninstall = job.with_name('uninstall_' + yaml_file).exists()
        has_description = Path(job.parent, 'files', yaml_file).exists()
        if has_uninstall and has_description:
            external_jobs[job_name] = str(job.parent)
    validation_add_jobs(validator, external_jobs)

    allowed_jobs = list(external_jobs if not validator.suite_args.whitelist else set(external_jobs) & validator.suite_args.whitelist)
    job_names = []
    agent_addresses = []
    for agent in installed_agents:
        agent_addresses.append([agent])
        job_names.append(sample(allowed_jobs, max(4, len(allowed_jobs))))
    validation_install_jobs(validator, job_names, agent_addresses)
    for names, addresses in zip(job_names, agent_addresses):
        for name, address in itertools.product(names, addresses):
            response = validation_state_job(validator, name, address)
            logger.debug('Last installation date: %s', response['install']['last_operation_date'])

    time.sleep(30)
    validation_uninstall_jobs(validator, job_names, agent_addresses)
    required_jobs = [
            ['fping', 'ip_route'],
            ['sysctl', 'tc_configure_link', 'time_series', 'histogram'],
            ['iperf3', 'd-itg_send', 'synchronization', 'owamp-client', 'nuttcp', 'ftp_clt', 'dashjs_client', 'voip_qoe_dest', 'voip_qoe_src', 'web_browsing_qoe'],
            ['iperf3', 'd-itg_recv', 'synchronization', 'owamp-server', 'nuttcp', 'ftp_srv', 'apache2', 'voip_qoe_dest', 'voip_qoe_src'],
    ]
    keep_jobs = installed_jobs | {j for jobs in required_jobs for j in jobs}
    validation_remove_jobs(validator, set(external_jobs) - keep_jobs)
    validation_install_jobs(validator, required_jobs, [list(installed_agents), [middlebox], [client], [server]])

    # Validate scenario-related functions
    with CWD.joinpath('scenario_stops.json').open() as f:
        scenario_name = json.load(f)['name']
    validation_add_scenario(validator, project_name, {
            'name': scenario_name,
            'description': 'simple scenario that stops itself',
            'openbach_functions': [],
    })
    validation_modify_scenario_from_file(validator, project_name, scenario_name, str(CWD / 'scenario_stops.json'))
    response = validation_add_scenario_from_file(validator, project_name, str(CWD / 'scenario_runs.json'))
    second_scenario_name = response['name']
    stops_itself_id = validation_start_scenario(validator, project_name, scenario_name)
    should_be_stopped_id = validation_start_scenario(validator, project_name, second_scenario_name)
    validation_status_scenario_stops(validator, stops_itself_id)
    validation_stop_scenario(validator, should_be_stopped_id)
    validation_status_scenario_stops(validator, should_be_stopped_id)
    with tempfile.TemporaryDirectory() as tempdir:
        validation_get_scenario_instance_data(validator, stops_itself_id, Path(tempdir))
    validation_remove_scenario(validator, project_name, scenario_name)
    validation_remove_scenario(validator, project_name, second_scenario_name)

    # Validate job-instances-related functions
    job_name = 'fping'
    instances_amount = 7  # Beware, not too high as the agent can't handle more than 10 tasks at once
    agent_address, = sample(list(installed_agents), 1)
    arguments = {'destination_ip': '127.0.0.1'}
    for _ in range(instances_amount):
        response = validation_start_job_instance(validator, job_name, agent_address, arguments)
    watched_job = response['job_instance_id']
    response = validation_list_job_instances(validator, agent_address)
    try:
        agent, = (a for a in response['instances'] if a['address'] == agent_address)
        job, = (j for j in agent['installed_jobs'] if j['job_name'] == job_name)
        instances = [i for i in job['instances'] if i['status'] == 'Running']
        if len(instances) != instances_amount:
            logger.warning(
                    'Expected %d running instances of %s but found %d instead', 
                    instances_amount, job_name, len(instances))
    except ValueError:
        logger.error('Error while getting number of instances for job %s', job_name)
    validation_stop_job_instance(validator, watched_job)
    validation_stop_all_job_instances(validator, agent_address)
    validation_status_job_instance_stops(validator, watched_job)

    # Setup routes between client and server to use the middlebox
    validation_start_job_instance(validator, 'ip_route', server, {
            'operation': 'add',
            'gateway_ip': validator.suite_args.middlebox_ip_server,
            'destination_ip': {'network_ip': '{}/32'.format(validator.suite_args.client_ip)}
    })
    validation_start_job_instance(validator, 'ip_route', client, {
            'operation': 'add',
            'gateway_ip': validator.suite_args.middlebox_ip_client,
            'destination_ip': {'network_ip': '{}/32'.format(validator.suite_args.server_ip)}
    })
    validation_start_job_instance(validator, 'sysctl', middlebox, {
            'parameter': 'net.ipv4.ip_forward',
            'value': '1',
    })

    # Run example executors
    logger.info('Running example executors:')

    logger.info('  Data transfer configure link')
    data_transfer_path = CWD.parent / 'executors' / 'examples' / 'data_transfer_configure_link.py'
    data_transfer_configure_link = load_executor_from_path(data_transfer_path)
    data_transfer_configure_link([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--entity', 'Middlebox',
        '--server', 'Server',
        '--client', 'Client',
        '--file-size', '10M',
        '--bandwidth-server-to-client', '10M',
        '--bandwidth-client-to-server', '10M',
        '--delay-server-to-client', '10',
        '--delay-client-to-server', '10',
        '--client-ip', validator.suite_args.client_ip,
        '--middlebox-interfaces', validator.suite_args.middlebox_interfaces,
        project_name, 'run',
    ])

    # Run reference executors
    logger.info('Running reference executors:')
    executors_path = CWD.parent / 'executors' / 'references'

    logger.info('  Network Delay')
    network_delay = load_executor_from_path(executors_path / 'executor_network_delay.py')
    network_delay([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--server-ip', validator.suite_args.server_ip,
        '--client-ip', validator.suite_args.client_ip,
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    logger.info('  Network Jitter')
    network_jitter = load_executor_from_path(executors_path / 'executor_network_jitter.py')
    network_jitter([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--server-ip', validator.suite_args.server_ip,
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    logger.info('  Network Rate')
    network_rate = load_executor_from_path(executors_path / 'executor_network_rate.py')
    network_rate([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--server-ip', validator.suite_args.server_ip,
        '--rate-limit', '10M',
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    # logger.info('  Network QOS')
    # network_qos = load_executor_from_path(executors_path / 'executor_network_qos.py')
    # network_qos([
    #     '--controller', controller,
    #     '--login', validator.credentials.get('login', ''),
    #     '--password', validator.credentials.get('password', ''),
    #     project_name, 'run',
    # ])

    logger.info('  Network One Way Delay')
    network_owd = load_executor_from_path(executors_path / 'executor_network_one_way_delay.py')
    network_owd([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--server-ip', validator.suite_args.server_ip,
        '--client-ip', validator.suite_args.client_ip,
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    logger.info('  Network Global')
    network_global = load_executor_from_path(executors_path / 'executor_network_global.py')
    network_global([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--server-ip', validator.suite_args.server_ip,
        '--client-ip', validator.suite_args.client_ip,
        '--rate-limit', '10M',
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    logger.info('  Service FTP')
    service_ftp = load_executor_from_path(executors_path / 'executor_service_ftp.py')
    service_ftp([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--server-ip', validator.suite_args.server_ip,
        '--mode', 'download',
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    logger.info('  Service Video Dash')
    service_dash = load_executor_from_path(executors_path / 'executor_service_video_dash.py')
    service_dash([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--server-ip', validator.suite_args.server_ip,
        '--duration', '30',
        '--launch-server',
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    logger.info('  Service VoIP')
    service_voip = load_executor_from_path(executors_path / 'executor_service_voip.py')
    service_voip([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--server-ip', validator.suite_args.server_ip,
        '--client-ip', validator.suite_args.client_ip,
        '--server-port', '8010',
        '--duration', '30',
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    logger.info('  Service Web Browsing')
    service_web = load_executor_from_path(executors_path / 'executor_service_web_browsing.py')

    service_web([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--duration', '30',
        '--url', 'https://{}:8081/website_openbach/www.openbach.org/content/home.php'.format(validator.suite_args.server_ip),
        '--url', 'https://{}:8082/website_cnes/cnes.fr/fr/index.html'.format(validator.suite_args.server_ip),
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    logger.info('  Service Traffic Mix')
    service_mix = load_executor_from_path(executors_path / 'executor_service_traffic_mix.py')
    service_mix([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--data-transfer', '1', 'Server', 'Client', '60', 'None', 'None', '0', validator.suite_args.server_ip, validator.suite_args.client_ip, '5201', '10M', '0', '1500',
        '--dash', '2', 'Server', 'Client', '60', 'None', 'None', '0', validator.suite_args.server_ip, validator.suite_args.client_ip, 'http/2', '5301',
        # To avoid proxy issues using config.yml, disable web-browsing
        # '--web-browsing', '3', 'Server', 'Client', '60', 'None', 'None', '0', validator.suite_args.server_ip, validator.suite_args.client_ip, '10', '2',
        '--voip', '4', 'Server', 'Client', '60', 'None', 'None', '0', validator.suite_args.server_ip, validator.suite_args.client_ip, '8011', 'G.711.1', '100.0', '120.0',
        '--data-transfer', '5', 'Server', 'Client', '60', '4', 'None', '5', validator.suite_args.server_ip, validator.suite_args.client_ip, '5201', '10M', '0', '1500',
        '--dash', '6', 'Server', 'Client', '60', '4', 'None', '5', validator.suite_args.server_ip, validator.suite_args.client_ip, 'http/2', '5301',
        # To avoid proxy issues using config.yml, disable web-browsing
        # '--web-browsing', '7', 'Server', 'Client', '60', '4', 'None', '5', validator.suite_args.server_ip, validator.suite_args.client_ip, '10', '2',
        '--voip', '8', 'Server', 'Client', '60', '4', 'None', '5', validator.suite_args.server_ip, validator.suite_args.client_ip, '8012', 'G.711.1', 'None', 'None',
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    logger.info('  Transport TCP One Flow')
    transport_oneflow = load_executor_from_path(executors_path / 'executor_transport_tcp_one_flow.py')
    transport_oneflow([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'Server',
        '--client-entity', 'Client',
        '--server-ip', validator.suite_args.server_ip,
        '--transmitted-size', '1G',
        '--post-processing-entity', 'Middlebox',
        project_name, 'run',
    ])

    # logger.info('  Transport TCP Stack Conf')
    # transport_stack = load_executor_from_path(executors_path / 'executor_transport_tcp_stack_conf.py')
    # transport_stack([
    #     '--controller', controller,
    #     '--login', validator.credentials.get('login', ''),
    #     '--password', validator.credentials.get('password', ''),
    #     project_name, 'run',
    # ])

    # Remove routes between client and server to use the middlebox
    validation_start_job_instance(validator, 'ip_route', server, {
            'operation': 'delete',
            'destination_ip': {'network_ip': '{}/32'.format(validator.suite_args.client_ip)}
    })
    validation_start_job_instance(validator, 'ip_route', client, {
            'operation': 'delete',
            'destination_ip': {'network_ip': '{}/32'.format(validator.suite_args.server_ip)}
    })

    # Cleanup
    validation_remove_project(validator, project_name)
    validation_uninstall_agents(validator, installed_agents)
    validation_install_agents(validator, free_agents)
    job_names = []
    agent_addresses = []
    for address, agent in free_agents.items():
        agent_addresses.append([address])
        job_names.append(agent['jobs'])
    validation_install_jobs(validator, job_names, agent_addresses)


if __name__ == '__main__':
    setup_logging()
    main(sys.argv[1:])
