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
#
# Author: Nicolas Kuhn / <nicolas.kuhn@cnes.fr>

# This script extracts a metric from a CSV and reset the time to
# a format that can easily be plot

import csv
import argparse
import datetime


def convert_time(row, time_column_id, time_format='%Y-%m-%d %H:%M:%S.%f%z'):
    return datetime.strptime(row[time_column_id], time_format)


def main(input_file, output_file, entity, metric_name, time_column_name='time', entity_column_name='@agent_name'):
    with open(input_file) as f:
        reader = csv.reader(f)
        header = next(reader)

        time_column_id = header.index(time_column_name)
        entity_column_id = header.index(entity_column_name)
        metric_column_id = header.index(metric_name)

        origin = min(convert_time(row, time_column_id) for row in reader)

    with open(input_file) as f, open(output_file, 'w') as w:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            value = row[column_id_metric]
            if row[entity_column_id] == entity and value:
                time = convert_time(row, time_column_id)
                elapsed = (time - origin).total_seconds()
                print(elapsed, value, file=w)


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-in', '--csvin', type=str, help='Name of the input CSV file')
    parser.add_argument('-out', '--txtout', type=str, help='Name of the ouptu TXT file')
    parser.add_argument('-e', '--entity', type=str, help='Entity name')
    parser.add_argument('-m', '--metric_name', type=str, help='Name of the metrics that is extracted')

    # get args
    args = parser.parse_args()
    csvin = args.csvin
    txtout = args.txtout
    entity = args.entity
    metric = args.metric_name

    # lauch main
    main(csvin, txtout, entity, metric)
