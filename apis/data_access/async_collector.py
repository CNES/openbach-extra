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

__author__ = 'Mathias ETTINGER <mettinger@toulouse.viveris.com>'
__all__ = ['AsyncCollectorConnection']

import asyncio
from functools import partial, wraps

from .collector import CollectorConnection


def _make_coroutine(function):
    @wraps(function)
    async def wrapper(self, *args, **kwargs):
        function_call = partial(function, self, *args, **kwargs)
        future = self.loop.run_in_executor(None, function_call)
        value = await future
        return value
    return wrapper


class MakeAsync(type):
    """Helper metaclass used to wrap public methods of base classes
    into coroutines.
    """

    def __new__(mcls, name, bases, dct):
        for base in bases:
            for name, function in vars(base).items():
                if not name.startswith('_') and callable(function):
                    dct[name] = _make_coroutine(function)

        return type.__new__(mcls, name, bases, dct)


class AsyncCollectorConnection(CollectorConnection, metaclass=MakeAsync):
    """Asynchronous wrapper over CollectorConnection.

    Each public method of the base class is wrapped into a
    coroutine and scheduled in an event loop using its
    run_in_executor method. The default executor is used so
    it is up to the user of this class to configure the
    proper executor as the default one for the loop.

    The event loop used by this class is asyncio's current
    loop, retrieved when building an instance.
    """

    def __init__(self, collector_ip,
                 elasticsearch_port=9200,
                 influxdb_port=8086,
                 database_name='openbach',
                 epoch='ms'):
        super().__init__(collector_ip, elasticsearch_port, influxdb_port, database_name, epoch)
        self.loop = asyncio.get_event_loop()
