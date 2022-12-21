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

import json
from types import SimpleNamespace

from . import openbach_functions


class Scenario:
    """Interface between Python code and JSON scenario definition.

    This class aims at reducing the boilerplate necessary when
    defining configuration files for OpenBach scenarios. Instances
    of this class represents a configuration file for a given
    scenario.
    """

    def __init__(self, name, description=None):
        """Construct an empty scenario with the given metadata"""

        if description is None:
            description = name

        self.name = name
        self.description = description
        self.arguments = {}
        self.constants = {}
        self.openbach_functions = []

    def add_argument(self, name, description):
        """Add an argument for this scenario"""

        self.arguments[name] = str(description)

    def add_arguments(self, **arguments):
        for name, description in arguments.items():
            self.add_argument(name, description)

    def remove_argument(self, name):
        """Remove the given argument from this scenario"""

        try:
            del self.arguments[name]
        except KeyError:
            pass

    def remove_arguments(self, *names):
        for name in names:
            self.remove_argument(name)

    def add_constant(self, name, value):
        """Associate a value to a constant for this scenario"""

        self.constants[name] = str(value)

    def add_constants(self, **constants):
        for name, value in constants.items():
            self.add_constant(name, value)

    def remove_constant(self, name):
        """Remove the given constant from this scenario"""

        try:
            del self.contants[name]
        except KeyError:
            pass

    def remove_constants(self, *names):
        for name in names:
            self.remove_constant(name)

    def add_function(self, name, wait_delay=0, wait_launched=None, wait_finished=None, label=None):
        """Add an openbach function to this scenario.

        The function will be started after all other functions in
        `wait_launched` are started and all other functions in
        `wait_finished` are completed. After these conditions are
        met (if any), an additional delay of `wait_delay` will be
        applied before the function starts.
        """

        wait_launched = check_and_build_waiting_list(wait_launched)
        wait_finished = check_and_build_waiting_list(wait_finished)

        factory = get_function_factory(name)
        function = factory(wait_launched, wait_finished, wait_delay, label)
        self.openbach_functions.append(function)
        return function

    def remove_function(self, function):
        """Remove the given function from this scenario.

        The function should be an object returned by
        `self.add_function(...)`.
        """

        try:
            self.openbach_functions.remove(function)
        except ValueError:
            pass

    def build(self):
        """Construct a dictionary representing this scenario.

        This dictionary is suitable to be written in a file as
        JSON data.
        """
        return {
            'name': self.name,
            'description': self.description,
            'arguments': self.arguments.copy(),
            'constants': self.constants.copy(),
            'openbach_functions': [
                f.build(self.openbach_functions, id)
                for id, f in enumerate(self.openbach_functions)
            ],
        }

    def write(self, filename):
        """Write the JSON representation of this scenario in
        the requested file.
        """

        with open(filename, 'w') as fp:
            json.dump(self.build(), fp)

    def __str__(self):
        return self.name

    @property
    def subscenarios(self):
        for function in self.openbach_functions:
            if isinstance(function, openbach_functions.StartScenarioInstance):
                scenario = function.scenario_name
                if isinstance(scenario, Scenario):
                    yield from scenario.subscenarios
                    yield scenario
        yield self

    def extract_function_id(self, *job_names, include_subscenarios=False, **filtered_jobs):
        def _unfiltered(openbach_function):
            return True
        jobs = set(job_names) | set(filtered_jobs)
        for function_id, openbach_function in enumerate(self.openbach_functions):
            if isinstance(openbach_function, openbach_functions.StartJobInstance):
                name = openbach_function.job_name
                if name in jobs and filtered_jobs.get(name, _unfiltered)(openbach_function):
                    yield [function_id]
            elif include_subscenarios and isinstance(openbach_function, openbach_functions.StartScenarioInstance):
                scenario = openbach_function.scenario_name
                if isinstance(scenario, Scenario):
                    for ids in scenario.extract_function_id(*job_names, include_subscenarios=include_subscenarios, **filtered_jobs):
                        yield [function_id] + ids

    def find_openbach_function(self, path):
        function = SimpleNamespace(scenario_name=self)
        for function_id in path:
            scenario = function.scenario_name
            function = scenario.openbach_functions[function_id]
        return function


def check_and_build_waiting_list(wait_on=None):
    """Check that each element container in the `wait_on` iterable
    is a proper openbach function. Raise `TypeError` otherwise.

    Return the `wait_on` iterable converted to a list.
    """

    wait_on = [] if wait_on is None else list(wait_on)
    if not all(isinstance(obj, openbach_functions.OpenBachFunction) for obj in wait_on):
        raise TypeError('can only wait on iterables of openbach functions')
    return wait_on


def get_function_factory(name):
    """Convert a name to the appropriate openbach function"""

    n = ''.join(name.title().split('_'))
    try:
        cls = getattr(openbach_functions, n)
    except AttributeError:
        cls = getattr(openbach_functions, name)
    assert issubclass(cls, openbach_functions.OpenBachFunction)
    return cls
