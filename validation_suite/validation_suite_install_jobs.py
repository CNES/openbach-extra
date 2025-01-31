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
from pathlib import Path

from validation_suite_utils import (
        InstallerBase,
        setup_logging,
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


class ValidationSuite(InstallerBase):
    PASSWORD_SENTINEL = object()

    def __init__(self):
        super().__init__()
        self.parser.add_argument(
                'entity', metavar='ADDRESS', nargs='+',
                help='address of the agents where the jobs are installed')
        self.parser.add_argument(
                '-j', '--job', action='append',
                help='job to add and install (may be specified '
                'several times, if missing all jobs are installed)')
        self.parser.add_argument(
                '-o', '--openbach-path', type=Path, default=CWD.parent.parent / "openbach",
                help='Path of jobs folder in OpenBACH repository')

    def parse(self, argv=None):
        args = super().parse(argv)
        openbach_path = CWD.joinpath(args.openbach_path).resolve()
        self.suite_args.agents = args.entity
        self.suite_args.jobs = args.job
        self.suite_args.openbach_path = openbach_path
        del args.job
        del args.entity
        del args.openbach_path

        if not openbach_path.is_dir():
            self.parser.error(f'openbach_path: {openbach_path} is not a directory')
        return args


def main(argv=None):
    logger = logging.getLogger(__name__)

    # Parse arguments
    validator = ValidationSuite()
    validator.parse(argv)
    controller = validator.args.controller
    agents = validator.suite_args.agents

    # Remove existing projects to add only ours
    project_name = 'Validation Suite Test Jobs'
    response = validation_list_projects(validator)
    for project in response:
        validation_remove_project(validator, project['name'])
    validation_create_project(validator, project_name)
    response = validation_get_project(validator, project_name)

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
    entities = {address: f'Entity {i}' for i, address in enumerate(agents)}
    for agent, name in entities.items():
        if agent not in installed_agents:
            logger.error('Agent %s is not installed', agent, exc_info=True)
            return
        validation_add_entity(validator, project_name, agent, name)

    # Install requested jobs on agents
    response = validation_list_jobs(validator)
    installed_jobs = {job['general']['name'] for job in response}
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

    required_jobs = jobs_list
    if validator.suite_args.jobs:
        try:
            required_jobs = {name: jobs_list[name] for name in validator.suite_args.jobs}
        except KeyError as job:
            logger.error("Job %s not found in openbach nor openbach-extra", job, exc_info=True)
            return
    validation_add_jobs(validator, required_jobs)
    validation_install_jobs(validator, [list(required_jobs)], [agents])
    logger.info("Requested %d job(s) install on %d agent(s)", len(required_jobs), len(agents))

    # Sanity check
    requested_jobs = set(required_jobs)
    response = validation_list_jobs(validator)
    added_jobs = {job['general']['name'] for job in response}
    logger.info("%d job(s) were added to the controller", len(added_jobs))
    missing_jobs = requested_jobs - added_jobs
    if missing_jobs:
        logger.warning("Job(s) not added: %s", missing_jobs)

    for agent, jobs in validation_list_installed_jobs(validator, agents):
        logger.info("%d job(s) were installed onto the agent %s", len(jobs), agent)
        missing_jobs = requested_jobs - set(jobs)
        if missing_jobs:
            logger.warning("Job(s) not added: %s", missing_jobs)


if __name__ == '__main__':
    setup_logging()
    main(sys.argv[1:])
