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


"""Sources of the Job wireguard"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Romain GUILLOTEAU <romain.guilloteau@viveris.fr>
'''

import sys
import syslog
import subprocess

from wireguard import command_line_parser, create_interface
import collect_agent


def delete_interface(tun_dev):
    cmd = ['ip', 'link', 'delete', tun_dev]
    try:
        p = subprocess.run(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error when deleting interface: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/wireguard/wireguard_rstats_filter.conf'):
        # Get args and call the appropriate function
        args = command_line_parser().parse_args()
        if args.function == create_interface:
            delete_interface(args.tun_dev)
