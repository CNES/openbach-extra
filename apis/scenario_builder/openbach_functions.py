#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

from .conditions import Condition


class ImproperlyConfiguredFunction(Exception):
    """Exception raised when an openbach function that has not been
    configured yet is used to build a scenario.
    """

    def __init__(self, name):
        super().__init__('{} has not been configured yet'.format(name))


class OpenBachFunction:
    """Base class for every OpenBach functions.

    Define the common boilerplate necessary to build their
    representation.
    """

    def __init__(self, launched, finished, delay, label=None):
        self.time = delay
        self.wait_launched = launched
        self.wait_finished = finished
        self.label = label
        self.fail_policy = {}

    def ignore_on_fail(self):
        self.fail_policy = {'policy': 'Ignore'}

    def fail_on_fail(self):
        self.fail_policy = {'policy': 'Fail'}

    def retry_on_fail(self, limit, delay=None):
        self.fail_policy = {
                'policy': 'Retry',
                'retry': limit,
        }
        if delay is not None:
            self.fail_policy['delay'] = delay

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        return {
                'id': function_id,
                'label': self.label if self.label else '#{}'.format(function_id),
                'wait': {
                    'time': self.time,
                    'launched_ids': list(safe_indexor(functions, self.wait_launched)),
                    'finished_ids': list(safe_indexor(functions, self.wait_finished)),
                },
                'on_fail': self.fail_policy,
        }


class StartJobInstance(OpenBachFunction):
    """Representation of the start_job_instance openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.start_job_instance = {}
        self.job_name = None

    def configure(self, job_name, entity_name, offset=None, interval=None, **job_arguments):
        """Define this openbach function with the mandatory values:
         - job_name: name of the job to start;
         - entity_name: name of the entity (hopefully with an agent
                        installed on) that should start the job;
         - offset: delay for the scheduler on the agent before starting
                   the job;
         - job_arguments: key=value pairs of arguments provided to
                          the job on the command line when starting it.
        """

        self.start_job_instance = {
                'entity_name': entity_name,
                job_name: job_arguments,
        }
        if offset is not None:
            self.start_job_instance['offset'] = offset
        if interval is not None:
            self.start_job_instance['interval'] = interval
        self.job_name = job_name

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.job_name is None:
            raise ImproperlyConfiguredFunction('start_job_instance')

        context = super().build(functions, function_id)

        job = self.job_name
        function = self.start_job_instance
        context['start_job_instance'] = {
            'entity_name': function['entity_name'],
            job: self._prepare_arguments(function[job], functions),
        }
        if function.get('offset') is not None:
            context['start_job_instance']['offset'] = function['offset']
        if function.get('interval') is not None:
            context['start_job_instance']['interval'] = function['interval']
 
        return context

    @staticmethod
    def _prepare_arguments(arguments, functions):
        if isinstance(arguments, dict):
            return {
                    key: StartJobInstance._prepare_arguments(value, functions)
                    for key, value in arguments.items()
            }
        elif isinstance(arguments, list):
            return [
                    StartJobInstance._prepare_arguments(arg, functions)
                    for arg in arguments
            ]
        elif isinstance(arguments, (StartJobInstance, StartScenarioInstance)):
            try:
                return next(safe_indexor(functions, [arguments]))
            except StopIteration:
                raise ImproperlyConfiguredFunction('start_job_instance')
        else:
            return arguments


class StopJobInstance(OpenBachFunction):
    """Representation of the stop_job_instance openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.openbach_function_indexes = ()

    def configure(self, *openbach_functions):
        """Define this openbach function with the mandatory values:
         - openbach_functions: list of openbach functions to stop.
        """

        if not all(isinstance(f, StartJobInstance) for f in openbach_functions):
            raise TypeError('{}.configure() arguments must '
                            'be StartScenarioInstance\'s '
                            'instances'.format(self.__class__.__name__))

        self.openbach_function_indexes = openbach_functions

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        context = super().build(functions, function_id)
        context['stop_job_instances'] = {
            'openbach_function_ids': list(
                safe_indexor(functions, self.openbach_function_indexes))}
        return context


class StartScenarioInstance(OpenBachFunction):
    """Representation of the start_scenario_instance openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.scenario_name = None

    def configure(self, scenario_name, **scenario_arguments):
        """Define this openbach function with the mandatory values:
         - scenario_name: name of the sub-scenario to start.
         - scenario_arguments: dictionary of arguments to use in
                               order to start the sub-scenario.
         - date: timestamp at which to start the sub-scenario.
                 [unused in OpenBach at the moment]
        """

        self.scenario_name = scenario_name
        self.scenario_arguments = scenario_arguments

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.scenario_name is None:
            raise ImproperlyConfiguredFunction('start_scenario_instance')

        context = super().build(functions, function_id)
        context['start_scenario_instance'] = {
            'scenario_name': str(self.scenario_name),
            'arguments': self.scenario_arguments,
        }
        return context


class StopScenarioInstance(OpenBachFunction):
    """Representation of the stop_scenario_instance openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.openbach_function_id = None

    def configure(self, openbach_function):
        """Define this openbach function with the mandatory values:
         - openbach_function: instance of the openbach function to
                              stop. This function must be a
                              StartScenarioInstance instance.
        """

        if not isinstance(openbach_function, StartScenarioInstance):
            raise TypeError('{}.configure() argument must '
                            'be a StartScenarioInstance '
                            'instance'.format(self.__class__.__name__))

        self.openbach_function_id = openbach_function

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.openbach_function_id is None:
            raise ImproperlyConfiguredFunction('stop_scenario_instance')

        ids = self.openbach_function_id,
        try:
            openbach_function_id, = safe_indexor(functions, ids)
        except ValueError:
            raise ValueError('configured function in stop_scenario_instance '
                             'does not reference a valid openbach_function '
                             'for this scenario') from None

        context = super().build(functions, function_id)
        context['stop_scenario_instance'] = {
            'openbach_function_id': openbach_function_id,
        }
        return context


class _Condition(OpenBachFunction):
    """Intermediate representation for openbach function
    that makes use of conditions.
    """

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.condition = None
        self.branch_true = ()
        self.branch_false = ()

    def configure(self, condition):
        """Define this openbach function with the mandatory values:
         - condition: test to execute during the scenario execution.
        """

        if not isinstance(condition, Condition):
            raise TypeError('{}.configure() argument should be an '
                            'instance of `Condition`'.format(
                            self.__class__.__name__))

        self.condition = condition

    def _check_openbach_functions(self, functions, name):
        if not all(isinstance(f, OpenBachFunction) for f in functions):
            raise TypeError('{}.{}() arguments must be OpenBachFunction\'s '
                            'instances'.format(self.__class__.__name__, name))

    def build(self, functions, function_id, name, branch_true_name, branch_false_name):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.condition is None:
            raise ImproperlyConfiguredFunction(name)

        context = super().build(functions, function_id)
        context[name] = {
            'condition': self.condition.build(functions),
            branch_true_name: list(safe_indexor(functions, self.branch_true)),
            branch_false_name: list(safe_indexor(functions, self.branch_false)),
        }
        return context


class If(_Condition):
    """Representation of the if openbach function."""

    def configure_if_true(self, *openbach_functions):
        """Define the functions to execute if the test evaluates
        to True during the scenario execution.
        """

        self._check_openbach_functions(openbach_functions, 'configure_if_true')
        self.branch_true = openbach_functions

    def configure_if_false(self, *openbach_functions):
        """Define the functions to execute if the test evaluates
        to False during the scenario execution.
        """

        self._check_openbach_functions(openbach_functions, 'configure_if_false')
        self.branch_false = openbach_functions

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        name_true = 'openbach_functions_true'
        name_false = 'openbach_functions_false'
        return super().build(functions, function_id, 'if', name_true, name_false)


class While(_Condition):
    """Representation of the while openbach function."""

    def configure_while_body(self, *openbach_functions):
        """Define the functions to execute if the test evaluates
        to True during the scenario execution.
        """

        self._check_openbach_functions(openbach_functions, 'configure_while_body')
        self.branch_true = openbach_functions

    def configure_while_end(self, *openbach_functions):
        """Define the functions to execute if the test evaluates
        to False during the scenario execution.
        """

        self._check_openbach_functions(openbach_functions, 'configure_while_end')
        self.branch_false = openbach_functions

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        name_true = 'openbach_functions_while'
        name_false = 'openbach_functions_end'
        return super().build(functions, function_id, 'while', name_true, name_false)


class PushFile(OpenBachFunction):
    """Representation of the push_file openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.arguments = None

    def configure(self, entity_name, controller_path, agent_path, users=(), groups=(), removes=()):
        """Define this openbach function with the mandatory values:
         - entity_name: name of the entity (hopefully with an agent
                        installed on) that should receive the file;
         - controller_path: path of the file to send, on the controller; can be a list;
         - agent_path: path where to store the file on the agent; can be a list;
        """
        self.arguments = {
                'entity_name': entity_name,
                'local_path': controller_path,
                'remote_path': agent_path,
        }

        if users:
            self.arguments['users'] = users

        if groups:
            self.arguments['groups'] = groups

        if removes:
            self.arguments['removes'] = removes

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.arguments is None:
            raise ImproperlyConfiguredFunction('push_file')

        context = super().build(functions, function_id)
        context['push_file'] = self.arguments.copy()
        return context


class PullFile(OpenBachFunction):
    """Representation of the pull_file openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.arguments = None

    def configure(self, entity_name, controller_path, agent_path, users=(), groups=(), removes=()):
        """Define this openbach function with the mandatory values:
         - entity_name: name of the entity (hopefully with an agent
                        installed on) that should receive the file;
         - controller_path: path of the file to send, on the controller; can be a list;
         - agent_path: path where to store the file on the agent; can be a list;
        """
        self.arguments = {
                'entity_name': entity_name,
                'local_path': controller_path,
                'remote_path': agent_path,
        }

        if users:
            self.arguments['users'] = users

        if groups:
            self.arguments['groups'] = groups

        if removes:
            self.arguments['removes'] = removes

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.arguments is None:
            raise ImproperlyConfiguredFunction('pull_file')

        context = super().build(functions, function_id)
        context['pull_file'] = self.arguments.copy()
        return context


def safe_indexor(reference, lookup):
    """Generate the index of each element of `lookup` in the
    `reference` array.

    Skip missing elements.
    """

    for element in lookup:
        try:
            yield reference.index(element)
        except ValueError:
            pass

class Reboot(OpenBachFunction):
    """Representation of the reboot openbach function."""

    def __init__(self, launched, finished, delay, label):
        super().__init__(launched, finished, delay, label)
        self.arguments = None

    def configure(self, entity_name, kernel):
        """Define this openbach function with the mandatory values:
         - entity_name: name of the entity who will reboot
         - kernel: kernel name on which we want to reboot
        """
        self.arguments = {
                'entity_name': entity_name,
                'kernel': kernel,
        }

    def build(self, functions, function_id):
        """Construct a dictionary representing this function.

        This dictionary is suitable to be included in the
        `openbach_functions` array of the associated scenario.
        """

        if self.arguments is None:
            raise ImproperlyConfiguredFunction('reboot')

        context = super().build(functions, function_id)
        context['reboot'] = self.arguments.copy()
        return context

