#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016 CNES
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


"""Frontend scripts base tools

Define a structure able to specify a parser and an
action to send to the OpenBACH backend.

This module provides the boilerplate around managing
users authentication and pretty-printing the response
from the backend.
"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''

import os
import fcntl
import socket
import struct
import pprint
import getpass
import datetime
import argparse
import warnings
from sys import exit
from time import sleep

import requests


PWD = os.path.dirname(os.path.abspath(__file__))


def get_interface():
    """Return the name of the first network interface found"""
    return next(filter('lo'.__ne__, os.listdir('/sys/class/net/')), 'lo')


def get_ip_address(ifname):
    """Return the IP address associated to the given interface"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])


def read_controller_ip(filename=os.path.join(PWD, 'controller')):
    default_ip = get_ip_address(get_interface())
    try:
        stream = open(filename)
    except OSError as e:
        message = (
                'File not found: \'{}\'. Using one of your '
                'IP address instead as the default: \'{}\'.'
                .format(filename, default_ip))
        warnings.warn(message, RuntimeWarning)
        return default_ip

    with stream:
        controller_ip = stream.readline().strip()

    if not controller_ip:
        message = (
                'Empty file: \'{}\'. Using one of your '
                'IP address instead as the default: \'{}\'.'
                .format(filename, default_ip))
        warnings.warn(message, RuntimeWarning)
        return default_ip

    return controller_ip


def pretty_print(response):
    """Helper function to nicely format the response
    from the server.
    """

    if response.status_code != 204:
        try:
            content = response.json()
        except ValueError:
            content = response.text
        pprint.pprint(content, width=120)

    response.raise_for_status()


class FrontendBase:
    WAITING_TIME_BETWEEN_STATES_POLL = 5  # seconds

    @classmethod
    def autorun(cls):
        self = cls()
        self.parse()
        self.execute()

    def __init__(self, description):
        self.parser = argparse.ArgumentParser(
                description=description,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        backend = self.parser.add_argument_group('backend')
        backend.add_argument(
                '--controller-ip', default=read_controller_ip(),
                help='address at which the collector is listening')
        backend.add_argument(
                '--login', '--username',
                help='username used to authenticate as')

        self.session = requests.Session()

    def parse(self):
        self.args = args = self.parser.parse_args()
        self.base_url = url = 'http://{}/openbach/'.format(args.controller_ip)
        login = args.login
        if login:
            credentials = {
                    'login': login,
                    'password': getpass.getpass('OpenBACH password: '),
            }
            response = self.session.post(url + 'login/', json=credentials)
            response.raise_for_status()

    def date_to_timestamp(self, fmt='%Y-%m-%d %H:%M:%S.%f'):
        date = getattr(self.args, 'date', None)
        if date is not None:
            try:
                date = datetime.datetime.strptime(date, fmt)
            except ValueError:
                self.parser.error(
                        'date and time does not respect '
                        'the {} format'.format(fmt))
            else:
                return int(date.timestamp() * 1000)

    def execute(self):
        pass

    def request(self, verb, route, show_response_content=True, **kwargs):
        verb = verb.upper()
        url = self.base_url + route
        if verb == 'GET':
            response = self.session.get(url, params=kwargs)
        else:
            response = self.session.request(verb, url, json=kwargs)
        if show_response_content:
            pretty_print(response)
        return response

    def wait_for_success(self, status=None, valid_statuses=(200, 204)):
        while True:
            sleep(self.WAITING_TIME_BETWEEN_STATES_POLL)
            response = self.query_state()
            response.raise_for_status()
            try:
                content = response.json()
            except ValueError:
                text = response.text
                code = response.status_code
                exit('Server returned non-JSON response with '
                     'status code {}: {}'.format(code, text))

            if status:
                content = content[status]
            returncode = content['returncode']
            if returncode != 202:
                pprint.pprint(content['response'], width=200)
                exit(returncode in valid_statuses)

    def query_state(self):
        return self.session.get(self.base_url)
