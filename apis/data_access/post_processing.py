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

"""Utilities to present data from an InfluxDB server and optionaly plot them.
"""

__author__ = 'Mathias ETTINGER <mettinger@toulouse.viveris.com>'
__all__ = ['save', 'Statistics']

import math
import pickle
import stat
import warnings
import itertools
from functools import partial
from contextlib import suppress
from datetime import datetime,timedelta

import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .influxdb_tools import (
        tags_to_condition, select_query,
        InfluxDBCommunicator, Operator,
        ConditionTag, ConditionAnd, ConditionOr,ConditionTimestamp,
)


DEFAULT_COLLECTOR_FILEPATH = '/opt/openbach/agent/collector.yml'


def _identity(x):
    return x


def _column_name_serializer(name):
    return '_'.join(map(str, name))


def _prepare_columns(df, columns):
    df = df.sort_values(['suffix', 'statistic'], axis=1)
    df.columns = [next(columns, name) or name for name in df.columns]
    return df


def influx_to_pandas(response, query):
    try:
        results = response['results']
    except KeyError:
        warnings.warn('The query \'{}\' returned no result, ignoring'.format(query))
        return

    for result in results:
        try:
            series = result['series']
        except KeyError:
            warnings.warn('The query \'{}\' result contained no time series, ignoring'.format(query))
            continue

        for serie in series:
            try:
                yield pd.DataFrame(serie['values'], columns=serie['columns'])
            except KeyError:
                warnings.warn('The query \'{}\' returned time series with no data, ignoring'.format(query))
                pass


def compute_histogram(bins):
    def _compute_histogram(series):
        histogram, _ = np.histogram(series.dropna(), bins)
        return histogram / histogram.sum()
        
    return _compute_histogram


def compute_annotated_histogram(bins):
    _hist = compute_histogram(bins)
    _bins = bins[1:]
    def _compute_annotated_histogram(series):
        return pd.DataFrame(_hist(series).reshape((1, -1)), index=[series.name], columns=_bins)
    return _compute_annotated_histogram


def save(figure, filename, use_pickle=False, set_legend=True):
    if use_pickle:
        with open(filename, 'wb') as storage:
            pickle.dump(figure, storage)
    else:
        for axis in figure.axes:
            if axis.get_legend() and set_legend:
                axis.legend(loc='center left', bbox_to_anchor=(1., .5))
        figure.savefig(filename, bbox_inches='tight')


def aggregator_factory(mapping):
    def aggregator(pd_datetime):
        for moment, intervals in mapping.items():
            if any(pd_datetime in interval for interval in intervals):
                return moment
        return 'Undefined'
    return aggregator


class Statistics(InfluxDBCommunicator):
    @classmethod
    def from_default_collector(cls, filepath=DEFAULT_COLLECTOR_FILEPATH):
        with open(filepath) as f:
            collector = yaml.safe_load(f)

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

    def _raw_influx_query(
            self, job=None, scenario=None, agent=None, job_instances=(),
            suffix=None, fields=None,timestamps=None, condition=None):

        if timestamps is not None:
            timestamp_condition = ConditionTimestamp.from_timestamps(timestamps)
            condition = timestamp_condition if condition is None else ConditionAnd(condition, timestamp_condition)

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
        return select_query(job, fields, _condition)

    def _parse_dataframes(self, response, query):
        offset = self.origin
        names = ['job', 'scenario', 'agent', 'suffix', 'statistic']
        for df in influx_to_pandas(response, query):
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
                extract = df.xs(index)
                if isinstance(extract, pd.Series):
                    extract = pd.DataFrame(extract.to_dict(), index=[0])
                section = extract.reset_index(drop=True).dropna(axis=1, how='all')
                section['time'] -= section.time[0] if offset is None else offset
                section.set_index('time', inplace=True)
                section.index.name = 'Time (ms)'
                section.reindex(columns=section.columns.sort_values())
                section.columns = pd.MultiIndex.from_tuples([index + (name,) for name in section.columns], names=names)
                yield section

    def fetch(
            self, job=None, scenario=None, agent=None, job_instances=(),
            suffix=None, fields=None,timestamps=None, condition=None):
        query = self._raw_influx_query(job, scenario, agent, job_instances, suffix, fields, timestamps,condition)
        data = self.sql_query(query)
        yield from (_Plot(df) for df in self._parse_dataframes(data, query))

    def fetch_all(
            self, job=None, scenario=None, agent=None, job_instances=(),
            suffix=None, fields=None, timestamps=None, condition=None, columns=None):
        query = self._raw_influx_query(job, scenario, agent, job_instances, suffix, fields,timestamps, condition)
        data = self.sql_query(query)
        df = pd.concat(self._parse_dataframes(data, query), axis=1)
        if not job_instances or columns is None:
            return _Plot(df)
        columns = iter(columns)
        return _Plot(pd.concat([_prepare_columns(df[id], columns) for id in job_instances if id in df], axis=1))


class _Plot:
    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.df = dataframe[dataframe.index >= 0]

    def _find_statistic(self, statistic_name=None, index=None):
        if statistic_name is not None:
            index = self.df.columns.get_level_values(4) == statistic_name

        if index is None:
            return self.df
        else:
            df = self.df.iloc[:, index]
            if isinstance(df, pd.DataFrame):
                return df
            else:
                return df.to_frame()

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

    def temporal_binning_statistics(
            self, statistic_name=None, index=None,
            time_aggregation='hour', percentiles=[.05, .25, .75, .95]):
        df = self._find_statistic(statistic_name, index)
        df.index = pd.to_datetime(df.index, unit='ms')
        
        for _, column in df.items():
            groups = column.groupby(getattr(column.index, time_aggregation))
            stats = groups.describe(percentiles=percentiles)
            stats.index.name = 'Time ({}s)'.format(time_aggregation)
            yield stats

    def temporal_binning_histogram(
            self, statistic_name=None, index=None, bin_size=100,
            offset=0, maximum=None, time_aggregation='hour',
            add_total=True, scale_factor=None):
        df = self._find_statistic(statistic_name, index)
        if scale_factor:
            df /= scale_factor
        
        df.index = pd.to_datetime(df.index, unit='ms')
        
        if maximum is None:
            nb_segments = math.ceil((df.max().max() - offset) / bin_size)
            maximum = nb_segments * bin_size + offset
        nb_segments = math.ceil((maximum - offset) / bin_size)

        bins = np.linspace(offset, maximum, nb_segments + 1, dtype='int')
        
        for _, column in df.items():
            cframe = column.to_frame()
            groups = cframe.groupby(getattr(cframe.index, time_aggregation))
            stats = groups.apply(compute_annotated_histogram(bins)) * 100
            stats.index = ['{}-{}'.format(i, i+1) for i in stats.index.droplevel()]
            stats.index.name = 'Time ({}s)'.format(time_aggregation)
            if add_total:
                total = cframe.apply(compute_histogram(bins)) * 100
                total.index = bins[1:]
                total.columns = ['total']
                yield pd.concat([stats, total.T])
            else:
                yield stats

    def compute_function(
            self, operation, scale_factor,
            start_day, start_evening, start_night,
            label_day='Journée', label_evening='Soirée', label_night='Nuit'):
        df = self.dataframe / scale_factor
        df.index = pd.to_datetime(df.index, unit='ms')

        earliest, midday, latest = sorted([
                (start_day, f'{label_day} ({start_day}h − {start_evening}h)'),
                (start_evening, f'{label_evening} ({start_evening}h − {start_night}h)'),
                (start_night, f'{label_night} ({start_night}h − {start_day}h)'),
        ])
        intervals = [(
            pd.Interval(pd.Timestamp(date), pd.Timestamp(date).replace(hour=earliest[0])),
            pd.Interval(pd.Timestamp(date).replace(hour=earliest[0]), pd.Timestamp(date).replace(hour=midday[0])),
            pd.Interval(pd.Timestamp(date).replace(hour=midday[0]), pd.Timestamp(date).replace(hour=latest[0])),
            pd.Interval(pd.Timestamp(date).replace(hour=latest[0]), pd.Timestamp(date) + pd.Timedelta(days=1)),
        ) for date in np.unique(df.index.date)]

        wrap_around, begin, middle, end = zip(*intervals)
        moments = aggregator_factory({
                earliest[1]: begin,
                midday[1]: middle,
                latest[1]: end + wrap_around,
        })

        aggregated = getattr(df, operation)(axis=1)
        grouped = aggregated.groupby(moments)
        return getattr(grouped, operation)()

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

    def plot_temporal_binning_statistics(
            self, axis=None, secondary_title=None,
            statistic_name=None, index=None,
            percentiles=[[5, 95], [25, 75]], time_aggregation='hour',
            median=True, average=True, deviation=True,
            boundaries=True, min_max=True, legend=True,grid=True):
        percentiles = sorted(percentiles or [], key=lambda x: abs(x[0] - x[1]), reverse=True)
        format_percentiles = [p / 100 for pair in percentiles for p in pair]

        temporal_binning = self.temporal_binning_statistics(
                statistic_name, index,
                time_aggregation, format_percentiles)

        if axis is None:
            _, axis = plt.subplots()
        colors = ['#ffad60', '#ffdae0']

        for stats in temporal_binning:
            if average:
                axis.plot(stats.index, stats['mean'], color='#005b96', label='average')
            if median:
                axis.plot(stats.index, stats['50%'], color='#be68be', label='median')
            if boundaries:
                axis.plot(stats.index, stats['min'], color='g', linewidth=1)
                axis.plot(stats.index, stats['max'], color='#e50000', linewidth=1)
            if min_max:
                axis.fill_between(stats.index, stats['min'], stats['max'], color='#39c9bb', label='min-max')
            for color, pair in zip(colors, percentiles):
                low, high = sorted(pair)
                axis.fill_between(
                        stats.index, stats['{}%'.format(low)],
                        stats['{}%'.format(high)], color=color,
                        label='{}%-{}%'.format(low, high))
            if deviation:        
                axis.errorbar(
                        stats.index, stats['mean'], stats['std'], uplims=True,
                        lolims=True, color='#005b96', elinewidth=1, label="deviation")
            if legend:
                axis.legend()

            if grid:
                axis.grid()
                
            axis.set_xlabel(stats.index.name)
            if secondary_title is not None:
                axis.set_ylabel(secondary_title)
        
        return axis

    def plot_temporal_binning_histogram(
            self, axis=None, secondary_title=None,
            statistic_name=None, index=None,
            bin_size=100, offset=0, maximum=None,
            time_aggregation='hour', add_total=True,
            legend=True, legend_title=None, legend_unit=None,
            colormap=None, scale_factor=None):
        temporal_binning = self.temporal_binning_histogram(
                statistic_name, index,
                bin_size, offset, maximum,
                time_aggregation, add_total,
                scale_factor)

        if axis is None:
            _, axis = plt.subplots()

        for stats in temporal_binning:
            cmap = plt.get_cmap(colormap)
            colors = cmap(np.linspace(0, 1, len(stats.columns)))
            xticks_size, xtick_weight = (5, 'bold') if len(stats.index) > 50 else (None, None)

            it_begin, it_end = itertools.tee(sorted(stats.columns), 2)
            it_begin = itertools.chain([0], it_begin)
            label = [f'{begin} − {end}' for begin, end in zip(it_begin, it_end)]
            for num, (index, segments) in enumerate(stats.iterrows()):
                starts = segments.cumsum() - segments
                if not num:
                   bars = axis.bar(index, segments, bottom=starts, width=0.5, label=label, color=colors, edgecolor='k', linewidth=0.1)
                else:
                   bars = axis.bar(index, segments, bottom=starts, width=0.5, color=colors, edgecolor='k', linewidth=0.1)

                axis.set_xticks(stats.index)
                axis.set_xticklabels(stats.index, rotation=90, fontsize=xticks_size, weight=xtick_weight)

            handles, labels = plt.gca().get_legend_handles_labels()
            if legend:
                title = legend_title or 'Legend'
                axis.legend(
                        reversed(handles), reversed(labels),
                        labelspacing=0.5,
                        title=f'{title} ({legend_unit})' if legend_unit else title,
                        loc='center left', bbox_to_anchor=(1., .5))
               
            axis.set_xlabel(stats.index.name)
            if secondary_title is not None:
                axis.set_ylabel(secondary_title)

        return axis
