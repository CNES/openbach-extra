#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2018 CNES
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


"""Sources of the Job web browsing qoe"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Francklin SIMO <francklin.simo@toulouse.viveris.com>
'''

import collect_agent
import syslog
import os
import yaml
import time
import argparse
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import FirefoxOptions


# TODO: Add support for other web browsers
def init_driver(binary_path, binary_type):
    """
    Method to initialize a Selenium driver. Only support Firefox browser for now.
    Args:
        binary_path(str): the path to the 'firefox' executable
        binary_type(str): for now, binary type can only be 'FirefoxBinary'.
    Returns:
        driver(WebDriver): an initialized Selenium WebDriver.
    """
    driver = None
    if binary_type == "FirefoxBinary":
        binary = FirefoxBinary(binary_path)
        opts = FirefoxOptions()
        opts.add_argument("--headless")
        driver = webdriver.Firefox(firefox_binary=binary, firefox_options=opts)
        driver.wait = WebDriverWait(driver, 5)
    return driver


def compute_qos_metrics(driver, url_to_fetch, qos_metrics):
    """
    Having retrieved the web page, this method computes QoS metrics by executing their associated javascript scripts.
    Args:
        driver(WebDriver): an initialized Selenium WebDriver.
        url_to_fetch(str): the url address to retrieve prior to compute the different metrics.
        qos_metrics(dict(str,str)): a dictionary where keys are metric names and values are javascript methods.
    Returns: 
        results(dict(str,object)): a dictionary containing the different metrics/values.
    """
    results = dict()
    driver.get(url_to_fetch)
    for key, value in qos_metrics.items():
        results[key] = driver.execute_script(value)
    return results
    
def print_qos_metrics(dict_to_print, config):
    """
    Helper method to print a dictionary of QoS metrics using their pretty names
    Args:
        dict_to_print(dict(str,str)): a dictionary where keys are metric labels and values are metric values 
        config(dict): a dictionary that should be the parsing result of the config.yaml file
    Returns:
        NoneType
    """
    for key, value in dict_to_print.items():
        print("{}: {} {}".format(config['qos_metrics'][key]['pretty_name'], value, config['qos_metrics'][key]['unit']))


def main(nb_runs):
    # Connect to collect agent
    conffile = '/opt/openbach/agent/jobs/web_browsing_qoe/web_browsing_qoe_rstats_filter.conf'
    success = collect_agent.register_collect(conffile)
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)
    # Init local variables
    qos_metrics_lists = dict()
    qos_metrics = dict()
    # Load config from config.yaml
    config = yaml.safe_load(open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.yaml')))
    for metric in config['qos_metrics']:
        qos_metrics[metric] = config['qos_metrics'][metric]['js']
    # Compute qos metrics for each url 'nb_runs' times
    for i in range(1, args.nb_runs + 1, 1):
        for url in config['web_pages_to_fetch']:
            binary_path = config['driver']['binary_path']
            binary_type =  config['driver']['binary_type']
            try:
                my_driver = init_driver(binary_path, binary_type)
            except Exception as ex:
                message = 'ERROR when initializing the web driver: {}'
                collect_agent.send_log(syslog.LOG_ERR, message.format(ex))
                exit(message)
            if my_driver is not None:
                s = "# Report for web page " + url + " #"
                print('\n' + s)
                timestamp = int(time.time() * 1000)
                my_qos_metrics = compute_qos_metrics(my_driver, url, qos_metrics)
                print_qos_metrics(my_qos_metrics, config)
                my_driver.quit()
                statistics = {'url':url}
                for key, value in my_qos_metrics.items():
                    statistics.update({key:value})
                collect_agent.send_stat(timestamp, **statistics)
                
            else:
                message = 'Sorry, specified driver is not available. For now, only Firefox driver is supported'
                collect_agent.send_log(syslog.LOG_ERR, message)
                exit(message)                
            time.sleep(5)

if __name__ == "__main__":
    
    # Argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("nb_runs", help="The number of fetches to perform for each website", type=int)
    args = parser.parse_args()
    
    main(args.nb_runs)
    