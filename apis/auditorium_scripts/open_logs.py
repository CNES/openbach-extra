#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2023 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.


""" Open closed logs in elastic search """


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquín MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''


import argparse
import calendar
import datetime

import requests

from auditorium_scripts.frontend import FrontendBase


def date(date, fmt='%d/%m/%Y'):
    """Parse a date to a datetime object"""
    return datetime.datetime.strptime(date, fmt).date()


def index_to_datetime(index):
    """Extract the timestamp of the index creation
    date out of the index informations.
    """
    timestamp = int(index['settings']['index']['creation_date'])
    return datetime.datetime.utcfromtimestamp(timestamp / 1000).date()


def date_past_years(relative_date, year_count):
    """Compute the date relative to an other, some years ago"""
    year = relative_date.year - year_count
    month = relative_date.month
    _, days_in_month = calendar.monthrange(year, month)
    day = min(relative_date.day, days_in_month)
    return datetime.date(year, month, day)


def date_past_months(relative_date, month_count):
    """Compute the date relative to an other, some months ago"""
    month = relative_date.month - month_count - 1
    year = relative_date.year + month // 12
    month = month % 12 + 1
    _, days_in_month = calendar.monthrange(year, month)
    day = min(relative_date.day, days_in_month)
    return datetime.date(year, month, day)


def date_past_days(relative_date, days_count):
    """Compute the date relative to an other, some days ago"""
    return relative_date - datetime.timedelta(days=days_count)


CONVERTERS = {
        'day': date_past_days,
        'days': date_past_days,
        'd': date_past_days,
        'month': date_past_months,
        'months': date_past_months,
        'm': date_past_months,
        'year': date_past_years,
        'years': date_past_years,
        'y': date_past_years,
}


class OpenLogs(FrontendBase):
    def __init__(self):
        self.parser = argparse.ArgumentParser(
                description='OpenBACH — Reopen Closed Logs in ElasticSearch',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        collector = self.parser.add_argument_group('collector')
        collector.add_argument(
                'collector_address',
                help='IP address of the collector running ElasticSearch')
        collector.add_argument(
                '-p', '--port', type=int, default=9200,
                help='port on which ElasticSearch is listening for HTTP requests')
        dates = self.parser.add_mutually_exclusive_group(required=True)
        dates.add_argument(
                '-d', '--date', nargs=2, type=date,
                help='dates between which the logs should be reopened. '
                'Format is DD/MM/YYYY')
        dates.add_argument(
                '-l', '--last', nargs=2, metavar=('DURATION', 'UNIT'),
                help='timespan from now to identify logs to reopen. e.g.: '
                '20 days, 3 months, or 1 year')

        self.session = requests.Session()

    def parse(self, args=None):
        self.args = args = self.parser.parse_args()
        last = args.last
        if last is None:
            args.date = sorted(args.date)


        duration, unit = last
        try:
            duration = int(duration)
        except ValueError:
            self.parser.error('argument -l: invalid duration value: \'{}\''.format(duration))

        now = datetime.datetime.now().date()
        try:
            start = CONVERTERS[unit](now, duration)
        except KeyError:
            parser.error('argument -l: invalid unit value: \'{}\''.format(unit))
        else:
            args.date = [start, now]

        self.base_url = 'http://{}:{}/'.format(args.collector_address, args.port)
        return args

    def execute(self, show_response_content=True):
        """Reopen closed logs on the collector that are between two dates"""

        # Get the list of all closed logs
        response = self.request(
                'GET', '_all/_settings',
                expand_wildcards='closed',
                show_response_content=False)
        response.raise_for_status()
        indices = response.json()

        # Check creation date of all
        to_open = ','.join(
                index
                for index, content in indices.items()
                if date_begin <= index_to_datetime(content) <= date_end
        )
        if not to_open:
            if show_response_content:
                print('Nothing to open in this date range')
            return

        # Open indexes
        return self.request(
                'POST', to_open + '/open',
                show_response_content=show_response_content)


if __name__ == '__main__':
    OpenLogs.autorun()
