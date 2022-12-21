#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#   
#   
#   Copyright © 2016-2023 CNES
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

""" Sources of the Job dashjs_client """

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import sys
import signal
import socket
import syslog
import argparse
import subprocess
from functools import partial

from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait

import collect_agent


HTTP1 = 'http/1.1'
HTTP2 = 'http/2'
DEFAULT_URL='{}://{}:{}/dash_content/?tornado_port={}'
DEFAULT_PATH='/dash_content/BigBuckBunny/2sec/BigBuckBunny_2s_simple_2014_05_09.mpd'

# The following variables *_PORT must have the same values as in installation file of the job 
# 'dashjs_player_server'. So don't change, unless you also change them in un/installation files 
# requiring to reinstall both jobs: 'dashjs_client' and 'dashjs_player_server'  on agents.

HTTP1_PORT = 8081
HTTP2_PORT = 8082


def isPortUsed(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        used = (s.connect_ex(('localhost', port)) == 0)
    return used


def close_all(driver, p_tornado, signum, frame):
    """ Closes the browser if open """
    driver.quit()
    p_tornado.terminate()
    p_tornado.wait()


def main(dst_ip, proto, tornado_port, path, time):
    if isPortUsed(tornado_port):
        message = "Port {} already used, cannot launch Tornado server. Aborting...".format(tornado_port)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    # Launch Tornado TODO add except ?
    p_tornado = subprocess.Popen([sys.executable, '/opt/openbach/agent/jobs/dashjs_client/tornado_server.py', '--port', str(tornado_port)])

    # Launch Firefox
    options = Options()
    options.add_argument('-headless')
    options.set_preference("network.websocket.allowInsecureFromHTTPS", True)
    driver = Firefox(executable_path='geckodriver', options=options)
    wait = WebDriverWait(driver, timeout=10)
    
    # Get page
    try:
        url_proto, port = ('http', HTTP1_PORT) if (proto == HTTP1) else ('https', HTTP2_PORT)
        driver.get(DEFAULT_URL.format(url_proto, dst_ip, port, tornado_port))

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
        close_all(driver, p_tornado, 0, 0)
        sys.exit(message)

    # Set signal handler
    close_all_partial = partial(close_all, driver, p_tornado)
    signal.signal(signal.SIGTERM, close_all_partial)
    signal.signal(signal.SIGALRM, close_all_partial)
    signal.alarm(time)

    signal.pause()


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/dashjs_client/dashjs_client.conf'):
        # Define usage
        parser = argparse.ArgumentParser(
                description='',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
        parser.add_argument(
                "dst_ip", type=str,
                help='The destination IP address')
        parser.add_argument(
                "protocol",  choices=[HTTP1, HTTP2],
                 help='The protocol to use by server to stream video')
        parser.add_argument(
                '-p', '--tornado_port', type=int, default=5301,
                help='Port used by the Tornado Server to get statistics from the DASH client (Default: 5301)')
        parser.add_argument(
                '-d', '--dir', type=str, default=DEFAULT_PATH,
                help='The path of the dir containing the video to stream')
        parser.add_argument(
                '-t', '--time', type=int, default=0,
                help='The duration (Default: 0 infinite')
        
        # Get arguments
        args = parser.parse_args()
        dst_ip = args.dst_ip
        proto = args.protocol
        tornado_port = args.tornado_port
        path = args.dir
        time = args.time
        
        main(dst_ip, proto, tornado_port, path, time)
