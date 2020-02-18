#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2019 CNES
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


"""Call the openbach-function push_file"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


from argparse import FileType

from auditorium_scripts.frontend import FrontendBase, pretty_print


class PushFile(FrontendBase):
    def __init__(self):
        super().__init__('OpenBACH — Push File')
        subparsers = self.parser.add_subparsers(title='action', help='action to perform')
        subparsers.required = True

        send = subparsers.add_parser('send', help='send file directly onto an agent')
        send.add_argument('agent', help='IP address of the agent')
        send.add_argument('remote_path', help='path where the file should be pushed')
        group = send.add_mutually_exclusive_group(required=True)
        group.add_argument('--path', help='path of the file on the controller')
        group.add_argument(
                '--local-file', type=FileType('r'),
                help='path of a file on the current '
                'computer to be sent to the agent')
        send.set_defaults(keep=False)

        keep = subparsers.add_parser('store', help='store file on the controller for future use')
        keep.add_argument('local_file', type=FileType('r'), help='path of the file to send to the controller')
        keep.add_argument('remote_path', help='path where the file should be stored')
        keep.set_defaults(keep=True)

    def execute(self, show_response_content=True):
        keep = self.args.keep
        form_data = {
                'path': self.args.remote_path,
                'keep_file': keep,
        }

        if not keep:
            form_data['agent_ip'] = self.args.agent

        local_file = self.args.local_file
        if local_file is not None:
            with local_file:
                response = self.session.post(
                        self.base_url + 'file',
                        data=form_data,
                        files={'file': local_file})
        else:
            form_data['local_path'] = self.args.path
            response = self.session.post(self.base_url + 'file', data=form_data)

        if show_response_content:
            pretty_print(response)
        return response


if __name__ == '__main__':
    PushFile.autorun()
