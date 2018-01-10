#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#   
#   
#   Copyright © 2017 CNES
#   
#   
#   This file is part of the OpenBACH testbed.
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

""" Sources of the Job dash client """

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import sys
import time
import syslog
import signal
import argparse
from functools import partial

import collect_agent
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait


DEFAULT_URL='http://{}:{}/vod-dash/'
DEFAULT_PORT=80
DEFAULT_PATH='/vod-dash/BigBuckBunny/2sec/BigBuckBunny_2s_simple_2014_05_09.mpd'


def close_firefox(driver, signum, frame):
    """ Closes the browser if open """
    driver.quit()

def main(dst_ip, port, path, time):
    # Connect to collect agent
    conffile = '/opt/openbach/agent/jobs/dash client/dash client.conf'
    collect_agent.register_collect(conffile)
 
    collect_agent.send_log(syslog.LOG_DEBUG, "About to launch Dash client")

    # Launch Firefox
    options = Options()
    options.add_argument('-headless')
    driver = Firefox(executable_path='geckodriver', firefox_options=options)
    wait = WebDriverWait(driver, timeout=10)
    
    # Get page
    try:
        driver.get(DEFAULT_URL.format(dst_ip, port))

        # Update path
        wait.until(expected.visibility_of_element_located((By.CSS_SELECTOR,
                'input.form-control:nth-child(3)'))).send_keys(Keys.CONTROL, 'a')
        wait.until(expected.visibility_of_element_located((By.CSS_SELECTOR,
                'input.form-control:nth-child(3)'))).send_keys(path)

        # Click Load
        wait.until(expected.visibility_of_element_located((By.CSS_SELECTOR,
            'span.input-group-btn > button:nth-child(2)'))).click()
    except WebDriverException as ex:
        message = "Exception with webdriver: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    # Set signal handler
    close_firefox_partial = partial(close_firefox, driver)
    signal.signal(signal.SIGTERM, close_firefox_partial)
    signal.signal(signal.SIGALRM, close_firefox_partial)
    signal.alarm(time)

    signal.pause()


if __name__ == "__main__":
    # Define usage
    parser = argparse.ArgumentParser(
            description='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            "dst_ip", type=str,
            help='The destination IP address')
    parser.add_argument(
            '-p', '--port', type=int, default=DEFAULT_PORT,
            help="The dst port")
    parser.add_argument(
            '-d', '--dir', type=str, default=DEFAULT_PATH,
            help='The path of the dir containing the video to stream')
    parser.add_argument(
            '-t', '--time', type=int, default=0,
            help='The duration (Default: 0 infinite')
    
    # Get arguments
    args = parser.parse_args()
    dst_ip = args.dst_ip
    path = args.dir
    time = args.time
    port = args.port
    
    main(dst_ip, port, path, time)
