#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016 CNES
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

"""OpenBach's Data Access utilities

This package aims at providing easy access to the various data
stored on behalf of OpenBach's jobs.

Statistics and logs are available through various methods as
well as means to filter them at will.
"""

__author__ = 'Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>'
__credits__ = 'contributions: Mathias ETTINGER'
__version__ = 'v0.1'
__all__ = [
    'read_scenario',
    'CollectorConnection',
    'AsyncCollectorConnection',
    'OperandStatistic',
    'OperandTimestamp',
    'OperandValue',
    'ConditionAnd',
    'ConditionOr',
    'ConditionEqual',
    'ConditionUpperOrEqual',
    'ConditionUpper',
    'ConditionNotEqual',
    'ConditionBelow',
    'ConditionBelowOrEqual',
]

from .collector_connection import (
    read_scenario,
    CollectorConnection,
    AsyncCollectorConnection,
)
from .result_filter import (
    OperandStatistic,
    OperandTimestamp,
    OperandValue,
    ConditionAnd,
    ConditionOr,
    ConditionEqual,
    ConditionUpperOrEqual,
    ConditionUpper,
    ConditionNotEqual,
    ConditionBelow,
    ConditionBelowOrEqual,
)
