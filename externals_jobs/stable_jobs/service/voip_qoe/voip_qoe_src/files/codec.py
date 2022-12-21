#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.

"""Sources of the codec.py file"""

__author__ = 'Antoine AUGER'
__credits__ = 'Antoine AUGER <antoine.auger@tesa.prd.fr>'

import sys
import yaml
import syslog
import os.path


class CodecConstants(object):
    """
    A CodecConstants object contains default and specific constants as defined by the ITU-T
    All values are set as class attributes to be easily accessed later
    """

    def load_default_constants(self, collect_agent, etc_dir_path):
        """
        Method to load default constants common to all codecs
        See https://www.itu.int/rec/T-REC-G.107-201506-I for default constants

        :param collect_agent: the OpenBACH collect agent
        :type collect_agent: object
        :param etc_dir_path: the path of the 'etc' config directory
        :type etc_dir_path: str
        :return: nothing
        """
        try:
            with open(os.path.join(etc_dir_path, 'default_constants.yml')) as stream:
                # We load default values
                default_constants = yaml.safe_load(stream)
            for key, val in default_constants.items():
                # We assign them to object attributes to use them
                setattr(self, str(key), float(val))
        except FileNotFoundError:
            message = 'Unable to find configuration file for default codec values'
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)

    def load_specific_constants(self, collect_agent, etc_dir_path, codec_name):
        """
        See https://www.itu.int/rec/T-REC-G.113-200711-I for codec-specific values

        :param collect_agent: the OpenBACH collect agent
        :type collect_agent: object
        :param etc_dir_path: the path to the *etc* directory that contains configuration files
        :type etc_dir_path: str
        :param codec_name: one of the supported codecs (G.711.1, G.711.2, G.723.1, G.729.2, G.729.3)
        :type codec_name: str
        :return: nothing
        """
        try:
            with open(os.path.join(etc_dir_path, "{}.yml".format(codec_name))) as stream:
                # We load specific values according to codec's name
                specific_constants = yaml.safe_load(stream)
            for key, val in specific_constants.items():
                # We assign them to object attributes to use them
                setattr(self, str(key), float(val))
        except FileNotFoundError:
            message = 'Unable to find configuration file for codec {}'.format(codec_name)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)

    def __init__(self, collect_agent, etc_dir_path, codec_name):
        """
        Constructor

        :param etc_dir_path: the path to the *etc* directory that contains configuration files
        :type etc_dir_path: str
        :param codec_name: one of the supported codecs (G.711.1, G.711.2, G.723.1, G.729.2, G.729.3)
        :type codec_name: str
        """
        self.load_default_constants(collect_agent, etc_dir_path)
        self.load_specific_constants(collect_agent, etc_dir_path, codec_name)
