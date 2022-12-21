#!/usr/bin/env python3

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


"""Restore the default configuration from /opt/openbach/agent/jobs/tcp_conf_linux/
at job uninstallation"""

from pathlib import Path


def restore_from(conf_file, dest_folder):
    with open(conf_file) as src:
        for line in src:
            name, value = line.split('=')
            with Path(dest_folder, *name.split('.')).open('w') as dest:
                dest.write(value)


if __name__ == '__main__':
    restore_from('/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf', '/proc/sys')
    restore_from('/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf', '/sys/module/tcp_cubic/parameters')
