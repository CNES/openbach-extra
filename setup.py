#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
    
setup(
    name="openbach-api",
    version="1.0.0",
    author="OpenBACH Team",
    author_email="admin@openbach.org",
    description=("OpenBACH API to build scenario JSONs and to access" \
                 "stats/log of the Collector data"),
    license="GPL",
    url="http://openbach.org",
    
    packages=find_packages()
)

