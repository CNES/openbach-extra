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

from pathlib import Path
from setuptools import setup, find_packages


def read(fname):
    with open(Path(__file__).parent / fname) as readme:
        return readme.read()


setup(
    name='openbach-api',
    version='3.11.5',
    author='OpenBACH Team',
    author_email='admin@openbach.org',
    description='OpenBACH API: build scenario JSONs and access Collector Data',
    long_description=read('README.md'),
    license='GPL',
    url='http://openbach.org',

    packages=find_packages(),
    install_requires=['requests', 'pandas', 'matplotlib'],

    test_suite='nose.collector',
    tests_require=['nose'],
)
