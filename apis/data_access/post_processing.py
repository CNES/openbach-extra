#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2019 CNES
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

"""Utilities to present data from an InfluxDB server and optionaly plot them.
"""

__author__ = 'Mathias ETTINGER <mettinger@toulouse.viveris.com>'
__all__ = ['save', 'Statistics']

import pickle
from functools import partial
from contextlib import suppress

import yaml
import numpy as np
import pandas as pd

from .influxdb_tools import (
        tags_to_condition, select_query,
        InfluxDBCommunicator, Operator,
        ConditionTag, ConditionAnd, ConditionOr,
)


DEFAULT_COLLECTOR_FILEPATH = '/opt/openbach/agent/collector.yml'


def _identity(x):
    return x


def _column_name_serializer(name):
    return '_'.join(map(str, name))


def influx_to_pandas(response):
    for result in response.get('results', []):
        for serie in result.get('series', []):
            with suppress(KeyError):
                yield pd.DataFrame(serie['values'], columns=serie['columns'])


def compute_histogram(bins):
    def _compute_histogram(series):
        histogram, _ = np.histogram(series.dropna(), bins)
        return histogram / histogram.sum()
    return _compute_histogram


def save(figure, filename, use_pickle=False):
    if use_pickle:
        with open(filename, 'wb') as storage:
            pickle.dump(figure, storage)
    else:
        figure.savefig(filename)


class Statistics(InfluxDBCommunicator):
    @classmethod
    def from_default_collector(cls, filepath=DEFAULT_COLLECTOR_FILEPATH):
        with open(filepath) as f:
            collector = yaml.load(f)

        influx = collector.get('stats', {})
        return cls(
                collector['address'],
                influx.get('query', 8086),
                influx.get('database', 'openbach'),
                influx.get('precision', 'ms'))


    @property
    def origin(self):
        with suppress(AttributeError):
            return self._origin

    @origin.setter
    def origin(self, value):
        if value is not None and not isinstance(value, int):
            raise TypeError('origin should be None or a timestamp in milliseconds')
        self._origin = value

    def _raw_influx_data(
            self, job=None, scenario=None, agent=None, job_instances=(),
            suffix=None, fields=None, condition=None):
        conditions = tags_to_condition(scenario, agent, None, suffix, condition)
        instances = [
                ConditionTag('@job_instance_id', Operator.Equal, job_id)
                for job_id in job_instances
        ]

        if not conditions and not instances:
            _condition = None
        elif conditions and not instances:
            _condition = conditions
        elif not conditions and instances:
            _condition = ConditionOr(*instances)
        else:
            _condition = ConditionAnd(conditions, ConditionOr(*instances))
        return self.sql_query(select_query(job, fields, _condition))

    def _parse_dataframes(self, response, columns=None):
        if columns is None:
            names = ['job', 'scenario', 'agent', 'suffix', 'statistic']
        else:
            names = None

        offset = self.origin
        for df in influx_to_pandas(response):
            converters = dict.fromkeys(df.columns, partial(pd.to_numeric, errors='coerce'))
            converters.pop('@owner_scenario_instance_id')
            converters.pop('@suffix', None)
            converters['@agent_name'] = _identity

            converted = [convert(df[column]) for column, convert in converters.items()]
            if '@suffix' in df:
                converted.append(df['@suffix'].fillna(''))
            else:
                converted.append(pd.Series('', index=df.index, name='@suffix'))
            df = pd.concat(converted, axis=1)

            df.set_index(['@job_instance_id', '@scenario_instance_id', '@agent_name', '@suffix'], inplace=True)
            for index in df.index.unique():
                section = df.xs(index).reset_index(drop=True).dropna(axis=1, how='all')
                section['time'] -= section.time[0] if offset is None else offset
                section.set_index('time', inplace=True)
                section.index.name = 'Time (ms)'
                renamed = [index + (name,) for name in section.columns] if columns is None else columns
                section.columns = pd.MultiIndex.from_tuples(renamed, names=names)
                yield section

    def fetch(
            self, job=None, scenario=None, agent=None, job_instances=(),
            suffix=None, fields=None, condition=None, columns=None):
        data = self._raw_influx_data(job, scenario, agent, job_instances, suffix, fields, condition)
        yield from (_Plot(df) for df in self._parse_dataframes(data, columns))

    def fetch_all(
            self, job=None, scenario=None, agent=None, job_instances=(),
            suffix=None, fields=None, condition=None, columns=None):
        data = self._raw_influx_data(job, scenario, agent, job_instances, suffix, fields, condition)
        df = pd.concat(self._parse_dataframes(data, columns), axis=1)
        return _Plot(df)


class _Plot:
    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.df = dataframe[dataframe.index >= 0]

    def time_series(self):
        df = self.dataframe.interpolate()
        return df[df.index >= 0]

    def histogram(self, buckets):
        r_min = self.df.min().min()
        r_max = self.df.max().max()
        bins = np.linspace(r_min, r_max, buckets + 1)
        histogram = compute_histogram(bins)
        df = self.df.apply(histogram)
        bins = (bins + np.roll(bins, -1)) / 2
        df.index = bins[:buckets]
        return df

    def cumulative_histogram(self, buckets):
        return self.histogram(buckets).cumsum()

    def comparison(self):
        mean = self.df.mean()
        std = self.df.std().fillna(0)
        df = pd.concat([mean, std], axis=1)
        df.columns = ['Ε', 'δ']
        return df

    def plot_time_series(self, axis=None, secondary_title=None, legend=True):
        axis = self.time_series().plot(ax=axis, legend=legend)
        if secondary_title is not None:
            axis.set_ylabel(secondary_title)
        return axis

    def plot_kde(self, axis=None, secondary_title=None, legend=True):
        axis = self.df.plot.kde(ax=axis, legend=legend)
        if secondary_title is not None:
            axis.set_xlabel(secondary_title)
        return axis

    def plot_histogram(self, axis=None, secondary_title=None, bins=100, legend=True):
        axis = self.histogram(bins).plot(ax=axis, ylim=[-0.01, 1.01], legend=legend)
        if secondary_title is not None:
            axis.set_xlabel(secondary_title)
        return axis

    def plot_cumulative_histogram(self, axis=None, secondary_title=None, bins=100, legend=True):
        axis = self.cumulative_histogram(bins).plot(ax=axis, ylim=[-0.01, 1.01], legend=legend)
        if secondary_title is not None:
            axis.set_xlabel(secondary_title)
        return axis

    def plot_comparison(self, axis=None, secondary_title=None, legend=True):
        df = self.comparison()
        axis = df.Ε.plot.bar(ax=axis, yerr=df.δ, rot=30, legend=legend)
        if secondary_title is not None:
            axis.set_ylabel(secondary_title)
        return axis
