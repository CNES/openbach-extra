#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016 CNES
#
#
#   This file is NOT part of the OpenBACH testbed.
#
#
#   OpenBACH is a free software : you can redistribute it and/or modify it under the
#   terms of the GNU General Public License as published by the Free Software
#   Foundation, either version 3 of the License, or (at your option) any later
#   version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
#   details.
#
#   You should have received a copy of the GNU General Public License along with
#   this program. If not, see http://www.gnu.org/licenses/.

""" Sources of the job Launch_WebPage """

__author__ = 'Thales Alenia Space'
__credits__ = '''Contributors:
 * Romain Barbau <romain.barbau@free.fr>
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import os
import sys
import syslog
import time
import argparse
import collect_agent



def main(url):
    # Connect to collect-agent
    conffile = "/opt/openbach/agent/jobs/Launch_WebPage/Launch_WebPage_rstats_filter.conf"
    collect_agent.register_collect(conffile)
    if not success:
        message = "ERROR connecting to collect-agent"
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job Launch_webpage')

    # Get the DISPLAY parameter on the agent.
    displayParameter = str(os.system("echo $DISPLAY"))
    # Launch the browser with the specified url.
    os.system("export DISPLAY=:"+displayParameter+" ; firefox " + url)

    # Send a statistic to know when we actually launch the browser.
    statistics = {'Launch': 1}
    collect_agent.send_stat(int(round(time.time() * 1000)), **statistics)


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(description='', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('url', metavar='url', type=str, help='', default="https://www.python.org/")
    # get args
    args = parser.parse_args()
    url = args.url

    main(url)
