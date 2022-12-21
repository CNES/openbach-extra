#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2023 CNES
#
#
#   This file is part of the OpenBACH testbed.
#
#
#   OpenBACH is a free software : you can redistribute it and/or modify it under
#   the terms of the GNU General Public License as published by the Free Software
#   Foundation, either version 3 of the License, or (at your option) any later
#   version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
#   details.
#
#   You should have received a copy of the GNU General Public License along with
#   this program. If not, see http://www.gnu.org/licenses/.

"""Generic tools to build helpers"""

import argparse
import functools
from collections import ChainMap


def filter_none(_=None, **kwargs):
    """Filter out entries in dictionnary whose associated values are None"""
    dictionnary = ChainMap(kwargs, _ or {})
    return {key: value for key, value in dictionnary.items() if value is not None}


class Validate(argparse.Action):
    """Class used to validate a multi-type entry on the command-line"""
    ENTITY_TYPE = None

    def __call__(self, parser, args, values, option_string=None): 
        if getattr(args, self.dest) == None:
            self.items = []

        try:
            entity = self.ENTITY_TYPE(*values)
        except TypeError as e:
            raise argparse.ArgumentError(self, str(e).split('__init__() ', 1)[-1])
        except ValueError as e:
            raise argparse.ArgumentError(self, e)
        self.items.append(entity)
        setattr(args, self.dest, self.items)


class ValidateOptional:
    """Mixin indicating that a multi-type entry on the command-line has optional arguments"""
    pass


def patch_print_help(parser):
    """Circumvent the fact that optional arguments need to define `nargs='*'` and that messes up the generated help from argparse"""
    def decorate(printer):
        @functools.wraps(printer)
        def wrapper(file=None):
            nargs = [action.nargs for action in parser._actions]

            for action in parser._actions:
                if isinstance(action, ValidateOptional):
                    action.nargs = None
            printer(file)

            for action, narg in zip(parser._actions, nargs):
                action.nargs = narg

        return wrapper

    parser.print_help = decorate(parser.print_help)
    parser.print_usage = decorate(parser.print_usage)
