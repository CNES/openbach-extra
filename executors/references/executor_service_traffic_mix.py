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

"""This executor builds or launches the *service_traffic_mix* scenario
from /openbach-extra/apis/scenario_builder/scenarios/
It is a complex executor configured by "executor_service_traffic_mix_arg.txt" file
which can mix several services scenarios such as video_dash, voip, web_browsing
and service_data_transfer in a flexible manner.
"""

import argparse

from scenario_builder.helpers.utils import patch_print_help, ValidateOptional
from scenario_builder.scenarios import service_traffic_mix
from auditorium_scripts.scenario_observer import ScenarioObserver


def _try_float(value):
    if value is None or value == "None":
        return None

    return float(value)


def _parse_waited_ids(ids):
    if ids == "None":
        return []
    return list(map(int, ids.split('-')))


def _prepare_argparse_arguments(validator):
    fields = validator.TRAFFIC_TYPE._fields
    return {
            'nargs': len(validator.VALIDATOR),
            'metavar': fields[:1] + fields[2:],
            'action': validator,
            'dest': 'traffic',
    }


class _Validate(argparse.Action):
    VALIDATOR = (int, None, None, int, _parse_waited_ids, _parse_waited_ids, int, None, None)
    TRAFFIC_TYPE = None
    TRAFFIC_NAME = None

    def __call__(self, parser, args, values, option_string=None):
        items = getattr(args, self.dest)
        if items is None:
            items = []
            setattr(args, self.dest, items)

        try:
            validated = [
                    argument if validate is None else validate(argument)
                    for validate, argument in zip(self.VALIDATOR, values)
            ]
        except ValueError as e:
            raise argparse.ArgumentError(self, e)

        validated.insert(1, self.TRAFFIC_NAME)
        try:
            argument = self.TRAFFIC_TYPE(*validated)
        except (ValueError, TypeError) as e:
            raise argparse.ArgumentError(self, e)

        existing_ids = {arg.id for arg in items}
        if argument.id in existing_ids:
            raise argparse.ArgumentError(self, 'duplicate traffic ID: {}'.format(argument.id))

        for dependency in argument.wait_launched + argument.wait_finished:
            if dependency not in existing_ids:
                raise argparse.ArgumentError(self, 'dependency {} not found for traffic ID {}'.format(dependency, argument.id))

        items.append(argument)


class ValidateVoip(_Validate):
    VALIDATOR = _Validate.VALIDATOR + (int, None, _try_float, _try_float)
    TRAFFIC_NAME = 'voip'
    TRAFFIC_TYPE = service_traffic_mix.VoipArguments


class ValidateWebBrowsing(_Validate, ValidateOptional):
    VALIDATOR = _Validate.VALIDATOR + (int, int, None)
    TRAFFIC_NAME = 'web_browsing'
    TRAFFIC_TYPE = service_traffic_mix.WebBrowsingArguments

    def __call__(self, parser, args, values, option_string=None):
        vals = values[:len(self.VALIDATOR) - 1]
        urls = values[len(self.VALIDATOR) - 1:]
        values = [*vals, urls or None]
        self.nargs = len(self.VALIDATOR)
        args_pattern = '%s' % ''.join('A' * len(values))
        parser._match_argument(self, args_pattern)
        return super().__call__(parser, args, values, option_string)


class ValidateDash(_Validate):
    VALIDATOR = _Validate.VALIDATOR + (None, int)
    TRAFFIC_NAME = 'dash'
    TRAFFIC_TYPE = service_traffic_mix.DashArguments


class ValidateDataTransfer(_Validate):
    VALIDATOR = _Validate.VALIDATOR + (int, None, int, int)
    TRAFFIC_NAME = 'data_transfer'
    TRAFFIC_TYPE = service_traffic_mix.DataTransferArguments


def main(argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--voip', **_prepare_argparse_arguments(ValidateVoip),
            help='add a VoIP traffic generator sub-scenario')
    observer.add_scenario_argument(
            '--dash', **_prepare_argparse_arguments(ValidateDash),
            help='add a Dash traffic generator sub-scenario')
    observer.add_scenario_argument(
            '--web-browsing', nargs='*', action=ValidateWebBrowsing, dest='traffic',
            metavar='id source destination duration wait_launched wait_finished wait_delay source_ip destination_ip run_count parallel_runs [url ...]',
            help='add a web browsing traffic generator sub-scenario')
    observer.add_scenario_argument(
            '--data-transfer', **_prepare_argparse_arguments(ValidateDataTransfer),
            help='add a data transfer traffic generator sub-scenario')
    observer.add_scenario_argument(
            '--post-processing-entity', help='The entity where the post-processing will be performed '
            '(histogram/time-series jobs must be installed) if defined')

    patch_print_help(observer.parser)

    args = observer.parse(argv, service_traffic_mix.SCENARIO_NAME)

    scenario = service_traffic_mix.build(
            args.traffic or [],
            args.post_processing_entity,
            scenario_name=args.scenario_name)

    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
