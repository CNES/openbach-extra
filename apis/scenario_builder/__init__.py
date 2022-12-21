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

"""OpenBach's Scenarios JSON Builder utilities

This package aims at providing an API to ease programmatic building of
JSON files used to describe and configure a scenario in the OpenBach
framework.

Creation and configuration of various OpenBach functions is done
through objects references rather than manual edition and indexing.
"""


__author__ = 'Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>'
__version__ = 'v0.6.2'
__all__ = [
    'Scenario', 'Condition', 'Operand',
    'ImproperlyConfiguredFunction',
]


from .core import Scenario
from .openbach_functions import ImproperlyConfiguredFunction
from .conditions import Condition, Operand
