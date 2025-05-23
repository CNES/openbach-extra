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
import sys
import json
import fcntl
import shlex
import socket
import struct
import pprint
import logging
import getpass
import datetime
import argparse
import warnings
from copy import copy
from time import sleep
from pathlib import Path
from urllib3 import Retry
from contextlib import suppress

import requests


LOG = logging.getLogger(__name__)
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


def get_interfaces():
    """Return the name of the first network interface found"""
    yield from (
            iface.name
            for iface in Path('/sys/class/net/').iterdir()
            if iface.name != 'lo')
    yield 'lo'


def get_ip_address(ifname):
    """Return the IP address associated to the given interface"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])


def get_default_ip_address():
    """Return the first public IP address found"""
    for iface in get_interfaces():
        with suppress(OSError):
            return get_ip_address(iface)


def read_controller_configuration(filename='controller'):
    default_ip = get_default_ip_address()
    try:
        stream = open(filename)
    except OSError:
        return default_ip, None, None, None, True

    with stream:
        try:
            content = json.load(stream)
        except json.JSONDecodeError:
            stream.seek(0)
            controller = stream.readline().strip()
            password = None
            login = None
            vault_password = None
        else:
            if isinstance(content, str):
                content = {'controller': content}
            if not isinstance(content, dict):
                message = (
                        'Content of the \'controller\' file '
                        'is valid JSON but neither a string '
                        'nor a dictionnary: will consider it '
                        'as an empty file.')
                warnings.warn(message, RuntimeWarning)
                content = {}
            controller = content.get('controller')
            password = content.get('password')
            login = content.get('login')
            vault_password = content.get('vault_password')

    should_warn = False
    if not controller:
        controller = default_ip
        should_warn = True

    return controller, login, password, vault_password, should_warn


def pretty_print(response, content=None, check_status=True):
    """Helper function to nicely format the response
    from the server.
    """

    if content is None:
        if response.status_code != 204:
            try:
                content = response.json()
            except ValueError:
                content = response.text

    if content:
        pprint.pprint(content, width=200)

    if check_status:
        response.raise_for_status()


class FromFileArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, line):
        if line.lstrip().startswith('#'):
            return []
        return shlex.split(line)


class FrontendBase:
    WAITING_TIME_BETWEEN_STATES_POLL = 5  # seconds
    SENTINEL = object()

    @classmethod
    def autorun(cls):
        self = cls()
        try:
            self.parse()
            self.execute()
        except requests.RequestException as error:
            error_message = str(error)
        except ActionFailedError as error:
            error_message = error.message
        else:
            print('Operation successfull')
            return

        sys.exit(error_message)

    def __init__(self, description):
        self.__filename = 'controller'
        controller_file = dict(zip(
            ('controller', 'login', 'password', 'vault_password', 'unspecified'),
            read_controller_configuration(self.__filename),
        ))
        self.parser = FromFileArgumentParser(
                description=description,
                epilog='Backend-specific arguments can be specified by '
                'providing a file called \'controller\' in the same folder '
                'than this script. This file can contain a JSON dictionary '
                'whose values will act as defaults for the arguments or '
                'some text whose first line will be interpreted as the '
                '\'controller\' argument default value. If no password is '
                'specified using either this file or the command-line, it '
                'will be prompted without echo.',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                fromfile_prefix_chars='@')
        backend = self.parser.add_argument_group('backend')
        backend.add_argument(
                '--ignore-controller-file', dest='use_controller_file',
                action='store_false', default=controller_file,
                help='Avoid parsing default values from the \'' + self.__filename + '\' file')
        backend.add_argument(
                '--controller',
                help='Controller IP address')
        backend.add_argument(
                '--login', '--username',
                help='OpenBACH username')
        backend.add_argument(
                '--password',
                nargs='?', const=self.SENTINEL,
                help='OpenBACH password')
        backend.add_argument(
                '--vault-password',
                nargs='?', const=self.SENTINEL,
                help='Ansible Vault password')

        self.credentials = {}

        self.session = requests.Session()
        self.session.mount('http://', requests.adapters.HTTPAdapter(
            max_retries=Retry(total=5, connect=3, redirect=1, allowed_methods=None, backoff_factor=0.2),
            pool_connections=50,
            pool_maxsize=50,
            pool_block=True,
        ))

    def parse(self, args=None):
        self.args = args = self.parser.parse_args(args)
        controller_unspecified = False

        if args.use_controller_file:
            for name, value in args.use_controller_file.items():
                if name == 'unspecified':
                    controller_unspecified = value
                else:
                    if getattr(args, name, None) is None:
                        setattr(args, name, value)
        if args.controller is None:
            self.parser.error(
                    'error: no controller was specified '
                    'and the default cannot be found')
        if controller_unspecified and args.controller == args.use_controller_file['controller']:
            message = (
                    'File not found or empty: \'{}\'. Using one of your '
                    'IP address instead as the default: \'{}\'.'
                    .format(self.__filename, args.controller))
            warnings.warn(message, RuntimeWarning)

        self.base_url = url = 'http://{}:8000/'.format(args.controller)

        self.credentials['controller'] = args.controller
        if args.login:
            if (password := args.password) is self.SENTINEL:
                password = getpass.getpass('OpenBACH password: ')
            self.credentials.update(login=args.login, password=password)
            if (vault_password := args.vault_password) is self.SENTINEL:
                vault_password = getpass.getpass('Ansible Vault Password: ')
            self.credentials.update(vault_password=vault_password)
            response = self.session.post(url + 'login/', json=self.credentials)
            response.raise_for_status()

        with suppress(AttributeError):
            del self.args.login
        with suppress(AttributeError):
            del self.args.password
        with suppress(AttributeError):
            del self.args.vault_password

        return args

    def share_state(self, other_cls):
        instance = other_cls()
        instance.session = self.session
        instance.base_url = self.base_url
        instance.args = copy(self.args)
        return instance

    def date_to_timestamp(self, fmt=DEFAULT_DATE_FORMAT):
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

    def execute(self, show_response_content=True):
        pass

    def request(self, verb, route, show_response_content=True, check_status=True, files=None, **kwargs):
        verb = verb.upper()
        url = self.base_url + route
        LOG.debug('%s %s %s', verb, url, kwargs)
        while True:
            if verb == 'GET':
                response = self.session.get(url, params=kwargs)
            else:
                if files is None:
                    response = self.session.request(verb, url, json=kwargs)
                else:
                    response = self.session.request(verb, url, data=kwargs, files=files)

            if response.status_code == 460:
                LOG.info('Request could not complete due to missing or wrong Vault password. Asking for it.')
                kwargs['vault_password'] = getpass.getpass('Ansible Vault Password: ')
            else:
                break

        if show_response_content:
            pretty_print(response, check_status=check_status)
        return response

    def wait_for_success(self, status=None, valid_statuses=(200, 204), show_response_content=True):
        while True:
            sleep(self.WAITING_TIME_BETWEEN_STATES_POLL)
            response = self.query_state()
            response.raise_for_status()
            try:
                content = response.json()
            except ValueError:
                raise ActionFailedError(
                        'Server returned non-JSON response: {}'.format(response.text),
                        response.status_code)

            if status:
                content = content[status]
            returncode = content['returncode']
            if returncode != 202:
                content_shown = content['response']
                if show_response_content and content_shown:
                    pprint.pprint(content_shown, width=200)
                if returncode not in valid_statuses:
                    raise ActionFailedError(**content)
                return response

    def query_state(self):
        return self.session.get(self.base_url)


class ActionFailedError(Exception):
    def __init__(self, response, returncode, **kwargs):
        super().__init__(response)
        self.message = response
