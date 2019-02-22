#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as readme:
        return readme.read()


setup(
    name='openbach-api',
    version='2.4.1',
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
