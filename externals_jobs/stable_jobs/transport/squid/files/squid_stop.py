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


"""Sources of the Job squid"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * alban FRICOT <alban.fricot@toulouse.viveris.com>
'''


import subprocess
import squid


if __name__ == "__main__":
    args = squid.parse_command_line()
    trans_proxy = args.trans_proxy
    source_addr = args.source_addr
    input_iface = args.input_iface

    # delete iptable rule with arguments
    cmd = "iptables -t nat -D PREROUTING -i {} -s {}/24 -p tcp --dport 80 -j REDIRECT --to-port {} ".format(input_iface, source_addr, trans_proxy)
    p = subprocess.Popen(cmd, shell=True)
    p.wait()

