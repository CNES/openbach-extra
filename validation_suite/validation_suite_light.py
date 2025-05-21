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

import sys
import logging
import textwrap
import tempfile
from pathlib import Path

from validation_suite_utils import (
        ValidationSuiteBase,
        json,
        setup_logging,
        load_executor_from_path,
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
        validation_list_installed_jobs,
        validation_list_jobs,
        validation_add_jobs,
        validation_install_jobs,
        validation_remove_jobs,
        validation_start_job_instance,
        validation_list_job_instances,
        validation_stop_job_instance,
        validation_status_job_instance_stops,
        validation_stop_all_job_instances,
        validation_add_scenario,
        validation_add_scenario_from_file,
        validation_modify_scenario_from_file,
        validation_start_scenario,
        validation_stop_scenario,
        validation_status_scenario_stops,
        validation_get_scenario_instance_data,
)


CWD = Path(__file__).resolve().parent

# TODO warning: with this script platform must be clean (or user agree to lose everything)
# TODO: agents must be installed

REQUIRED_JOBS = {
        "default_admin": {
            "server": ["send_logs", "send_stats", "synchronization"],  # "kernel_compile"
            "middlebox": ["send_logs", "send_stats", "synchronization"],  # "kernel_compile"
            "client": ["send_logs", "send_stats", "synchronization"],  # "kernel_compile"
        },
        "default_post_processing": {
            "server": [
                "temporal_binning_statistics",
                "temporal_binning_histogram",
                "histogram", "comparison",
                "pcap_postprocessing",
                "time_series",
            ],
            "middlebox": [
                "temporal_binning_statistics",
                "temporal_binning_histogram",
                "histogram", "comparison",
                "pcap_postprocessing",
                "time_series",
            ],
            "client": [
                "temporal_binning_statistics",
                "temporal_binning_histogram",
                "histogram", "comparison",
                "pcap_postprocessing",
                "time_series",
            ],
        },
        "tests_json": {
            "server": ["ip_route", "fping"],
            "middlebox": ["ip_route", "sysctl"],
            "client": ["ip_route"],
        },
        "data_transfer_configure_link": {
            "server": ["iperf3"],
            "middlebox": ["tc_configure_link"],
            "client": ["iperf3"],
        },
        "network_delay": {
            "server": ["d-itg_recv", "synchronization"],
            "middlebox": ["time_series", "histogram"],
            "client": ["fping", "d-itg_send", "synchronization"],
        },
        "network_jitter": {
            "server": ["owamp-server", "synchronization"],
            "middlebox": ["time_series", "histogram"],
            "client": ["owamp-client", "synchronization"],
        },
        "network_rate": {
            "server": ["iperf3", "nuttcp", "synchronization"],
            "middlebox": ["time_series", "histogram"],
            "client": ["iperf3", "nuttcp", "synchronization"],
        },
        "network_owd": {
            "server": ["d-itg_recv", "owamp-server", "synchronization"],
            "middlebox": ["time_series", "histogram"],
            "client": ["d-itg_send", "owamp-client", "synchronization"],
        },
        "network_global": {
            "server": ["iperf3", "nuttcp", "d-itg_recv", "owamp-server", "synchronization"],
            "middlebox": ["time_series", "histogram"],
            "client": ["iperf3", "nuttcp", "fping", "d-itg_send", "owamp-client", "synchronization"],
        },
        "service_ftp": {
            "server": ["ftp_srv"],
            "middlebox": ["time_series", "histogram"],
            "client": ["ftp_clt"],
        },
        "service_dash": {
            "server": ["apache2"],
            "middlebox": ["time_series", "histogram"],
            "client": ["dashjs_client"],
        },
        "service_voip": {
            "server": ["voip_qoe_dest"],
            "middlebox": ["time_series", "histogram"],
            "client": ["voip_qoe_src"],
        },
        "service_web": {
            "server": ["apache2"],
            "middlebox": ["time_series", "histogram"],
            "client": ["web_browsing_qoe"],
        },
        "transport_oneflow": {
            "server": ["iperf3"],
            "middlebox": ["time_series", "histogram"],
            "client": ["iperf3"],
        },
}


class ValidationSuite(ValidationSuiteBase):
    def __init__(self):
        super().__init__()
        self.parser.add_argument(
                '-k', '--keep-installed-jobs', action='store_true',
                help='If enabled, jobs with are kept on agents. Jobs are installed only if not on agent. '
                'Otherwise, remove installed jobs from controller and reinstall only needed.')
        self.parser.add_argument(
                '-o', '--openbach-path', type=Path, default=CWD.parent.parent / "openbach",
                help='Path of jobs folder in OpenBACH repository')

    def parse(self, argv=None):
        args = super().parse(argv)
        openbach_path = CWD.joinpath(args.openbach_path).resolve()
        self.suite_args.keep_installed_jobs = args.keep_installed_jobs
        self.suite_args.openbach_path = openbach_path
        del args.keep_installed_jobs
        del args.openbach_path

        if not openbach_path.is_dir():
            self.parser.error(f'openbach_path: {openbach_path} is not a directory')
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

    # Remove existing projects to add only ours
    project_name = 'Validation Suite Light'
    response = validation_list_projects(validator)
    for project in response:
        validation_remove_project(validator, project['name'])
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

    # Prepare agents for further tests
    response = validation_list_agents(validator)
    validation_uninstall_agents(validator, [
            agent['address']
            for agent in response
            if agent['project'] is not None
    ])
    free_agents = {
            agent['address']: {'name': agent['name'], 'collector': agent['collector_ip']}
            for agent in response
            if not agent['project'] and not agent['reserved'] and agent['address'] != controller
    }
    existing_names = {agent['name'] for agent in response}
    validation_install_agents(validator, free_agents)
    installed_agents = {address: agent['name'] for address, agent in free_agents.items()}

    # Attach agents to entities
    entities = {
            client: "client",
            server: "server",
            middlebox: "middlebox",
    }
    for agent, name in entities.items():
        if agent not in installed_agents:
            logger.error('Agent %s is not installed', agent, exc_info=True)
            return
        validation_add_entity(validator, project_name, agent, name)

    # Prepare jobs for further tests
    response = validation_list_jobs(validator)
    installed_jobs = {job['general']['name'] for job in response}
    if not validator.suite_args.keep_installed_jobs:
        validation_remove_jobs(validator, installed_jobs)

    jobs_list = {}
    stable_jobs = CWD.parent / 'externals_jobs' / 'stable_jobs'
    core_jobs = validator.suite_args.openbach_path / 'src' / 'jobs'
    for folder in (stable_jobs, core_jobs):
        for job in folder.glob('**/install_*.yml'):
            job_name = job.stem[len('install_'):]
            yaml_file = '{}.yml'.format(job_name)
            has_uninstall = job.with_name('uninstall_' + yaml_file).exists()
            has_description = Path(job.parent, 'files', yaml_file).exists()
            if has_uninstall and has_description:
                jobs_list[job_name] = job.parent.as_posix()

    required_jobs = {
            job
            for scenario in REQUIRED_JOBS.values()
            for jobs in scenario.values()
            for job in jobs
    }
    missing_jobs = required_jobs - set(jobs_list)
    for job in missing_jobs:
        logger.error("Job %s not found in openbach nor openbach-extra", job, exc_info=True)
    validation_add_jobs(validator, {job: files for job, files in jobs_list.items() if job in required_jobs})

    # Install missing jobs on agents
    jobs_per_agent = dict(validation_list_installed_jobs(validator, entities))
    jobs_needed_per_agent = {
            address: list(
                {job for scenario in REQUIRED_JOBS.values() for job in scenario[agent]}
                - set(jobs_per_agent[address])
            )
            for address, agent in entities.items()
    }
    job_names = list(jobs_needed_per_agent.values())
    agent_addresses = [[address] for address in jobs_needed_per_agent]
    validation_install_jobs(validator, job_names, agent_addresses)

    # Validate scenario-related functions
    with CWD.joinpath('scenario_stops_light.json').open() as f:
        scenario_name = json.load(f)['name']
    validation_add_scenario(validator, project_name, {
            'name': scenario_name,
            'description': 'simple scenario that stops itself',
            'openbach_functions': [],
    })
    validation_modify_scenario_from_file(validator, project_name, scenario_name, str(CWD / 'scenario_stops_light.json'))
    response = validation_add_scenario_from_file(validator, project_name, str(CWD / 'scenario_runs_light.json'))
    second_scenario_name = response['name']
    stops_itself_id = validation_start_scenario(validator, project_name, scenario_name)
    should_be_stopped_id = validation_start_scenario(validator, project_name, second_scenario_name)
    validation_status_scenario_stops(validator, stops_itself_id)
    validation_stop_scenario(validator, should_be_stopped_id)
    validation_status_scenario_stops(validator, should_be_stopped_id)
    with tempfile.TemporaryDirectory() as tempdir:
        validation_get_scenario_instance_data(validator, stops_itself_id, Path(tempdir))

    # Validate job-instances-related functions
    job_name = 'fping'
    instances_amount = 7  # Beware, not too high as the agent can't handle more than 10 tasks at once
    arguments = {'destination_ip': '127.0.0.1'}
    for _ in range(instances_amount):
        response = validation_start_job_instance(validator, job_name, server, arguments)
    watched_job = response['job_instance_id']
    response = validation_list_job_instances(validator, server)
    try:
        agent, = (a for a in response['instances'] if a['address'] == server)
        job, = (j for j in agent['installed_jobs'] if j['job_name'] == job_name)
        instances = [i for i in job['instances'] if i['status'] == 'Running']
        if len(instances) != instances_amount:
            logger.warning(
                    'Expected %d running instances of %s but found %d instead', 
                    instances_amount, job_name, len(instances))
    except ValueError:
        logger.error('Error while getting number of instances for job %s', job_name)
    validation_stop_job_instance(validator, watched_job)
    validation_stop_all_job_instances(validator, server)
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
        '--entity', 'middlebox',
        '--server', 'server',
        '--client', 'client',
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
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', validator.suite_args.server_ip,
        '--client-ip', validator.suite_args.client_ip,
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Network Jitter')
    network_jitter = load_executor_from_path(executors_path / 'executor_network_jitter.py')
    network_jitter([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', validator.suite_args.server_ip,
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Network Rate')
    network_rate = load_executor_from_path(executors_path / 'executor_network_rate.py')
    network_rate([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', validator.suite_args.server_ip,
        '--rate-limit', '10M',
        '--post-processing-entity', 'middlebox',
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
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', validator.suite_args.server_ip,
        '--client-ip', validator.suite_args.client_ip,
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Network Global')
    network_global = load_executor_from_path(executors_path / 'executor_network_global.py')
    network_global([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', validator.suite_args.server_ip,
        '--client-ip', validator.suite_args.client_ip,
        '--rate-limit', '10M',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Service FTP')
    service_ftp = load_executor_from_path(executors_path / 'executor_service_ftp.py')
    service_ftp([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', validator.suite_args.server_ip,
        '--mode', 'download',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Service Video Dash')
    service_dash = load_executor_from_path(executors_path / 'executor_service_video_dash.py')
    service_dash([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', validator.suite_args.server_ip,
        '--duration', '30',
        '--launch-server',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Service VoIP')
    service_voip = load_executor_from_path(executors_path / 'executor_service_voip.py')
    service_voip([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', validator.suite_args.server_ip,
        '--client-ip', validator.suite_args.client_ip,
        '--server-port', '8010',
        '--duration', '30',
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    logger.info('  Service Web Browsing')
    service_web = load_executor_from_path(executors_path / 'executor_service_web_browsing.py')
    service_web([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--duration', '30',
        '--url', 'https://{}:8081/website_openbach/www.openbach.org/content/home.php'.format(validator.suite_args.server_ip),
        '--url', 'https://{}:8082/website_cnes/cnes.fr/fr/index.html'.format(validator.suite_args.server_ip),
        '--post-processing-entity', 'middlebox',
        project_name, 'run',
    ])

    # logger.info('  Service Traffic Mix')
    # service_mix = load_executor_from_path(executors_path / 'executor_service_traffic_mix.py')
    # service_mix([
    #     '--controller', controller,
    #     '--login', validator.credentials.get('login', ''),
    #     '--password', validator.credentials.get('password', ''),
    #     '--data-transfer', '1', 'server', 'Client', '60', 'None', 'None', '0', validator.suite_args.server_ip, validator.suite_args.client_ip, '5201', '10M', '0', '1500',
    #     '--dash', '2', 'server', 'client', '60', 'None', 'None', '0', validator.suite_args.server_ip, validator.suite_args.client_ip, 'http/2', '5301',
    #     # To avoid proxy issues using config.yml, disable web-browsing
    #     # '--web-browsing', '3', 'server', 'client', '60', 'None', 'None', '0', validator.suite_args.server_ip, validator.suite_args.client_ip, '10', '2',
    #     '--voip', '4', 'server', 'client', '60', 'None', 'None', '0', validator.suite_args.server_ip, validator.suite_args.client_ip, '8011', 'G.711.1', '100.0', '120.0',
    #     '--data-transfer', '5', 'server', 'client', '60', '4', 'None', '5', validator.suite_args.server_ip, validator.suite_args.client_ip, '5201', '10M', '0', '1500',
    #     '--dash', '6', 'server', 'client', '60', '4', 'None', '5', validator.suite_args.server_ip, validator.suite_args.client_ip, 'http/2', '5301',
    #     # To avoid proxy issues using config.yml, disable web-browsing
    #     # '--web-browsing', '7', 'server', 'client', '60', '4', 'None', '5', validator.suite_args.server_ip, validator.suite_args.client_ip, '10', '2',
    #     '--voip', '8', 'server', 'client', '60', '4', 'None', '5', validator.suite_args.server_ip, validator.suite_args.client_ip, '8012', 'G.711.1', 'None', 'None',
    #     '--post-processing-entity', 'middlebox',
    #     project_name, 'run',
    # ])

    logger.info('  Transport TCP One Flow')
    transport_oneflow = load_executor_from_path(executors_path / 'executor_transport_tcp_one_flow.py')
    transport_oneflow([
        '--controller', controller,
        '--login', validator.credentials.get('login', ''),
        '--password', validator.credentials.get('password', ''),
        '--server-entity', 'server',
        '--client-entity', 'client',
        '--server-ip', validator.suite_args.server_ip,
        '--transmitted-size', '1G',
        '--post-processing-entity', 'middlebox',
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


if __name__ == '__main__':
    setup_logging()
    main(sys.argv[1:])
