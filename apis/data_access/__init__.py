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

"""OpenBach's Data Access utilities

This package aims at providing easy access to the various data
stored on behalf of OpenBach's jobs.

Statistics and logs are available through various methods as
well as means to filter them at will.
"""


__author__ = 'Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>'
__credits__ = 'Maintainer: Mathias ETTINGER <mettinger@toulouse.viveris.com>'
__version__ = 'v1.10.4'
__all__ = [
    'read_scenario',
    'CollectorConnection',
    'AsyncCollectorConnection',
    'Operator',
    'ConditionAnd',
    'ConditionOr',
    'ConditionTag',
    'ConditionField',
    'ConditionTimestamp',
    'Timeout',
]


from requests.exceptions import Timeout

from .result_data import read_scenario
from .async_collector import AsyncCollectorConnection, CollectorConnection
from .influxdb_tools import (Operator, ConditionAnd, ConditionOr, ConditionTag,
                             ConditionField, ConditionTimestamp)
