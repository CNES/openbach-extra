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


"""Sources of the Job random web browsing qoe"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Francklin SIMO <francklin.simo@toulouse.viveris.com>
'''

import os
import yaml
import time
import psutil
import syslog
import random
import signal 
import argparse
from functools import partial

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver import FirefoxOptions

import collect_agent


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
        try:
            binary = FirefoxBinary(binary_path)
           options = FirefoxOptions()
           # Disable notifications
           options.add_argument("--disable-notifications")
           options.add_argument("--headless")
           driver = webdriver.Firefox(firefox_binary=binary, options=options)
        except Exception as ex:
            message = 'ERROR when initializing the web driver: {}'.format(ex)
           collect_agent.send_log(syslog.LOG_ERR, message)
           exit(message)
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
    try:
        driver.get(url_to_fetch)
      for key, value in qos_metrics.items():
          results[key] = driver.execute_script(value)
    except Exception as ex:
        print(type(ex))
           message = 'An unexpected error occured: {}'.format(ex)
           collect_agent.send_log(syslog.LOG_WARNING, message)
           print(message)
    finally:
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


def choose_page_to_visit(driver):
    """
    Randomly select a page url from the list of url of clickable elements on current page
    """
    urls= list()
    for clickable_element in driver.find_elements_by_xpath('.//a'):
        try:
            url = clickable_element.get_attribute('href')
           urls.append(url)
        # Handle StaleElementReferenceException
        except Exception as ex:
            pass     
    selected_page = None
    notselected_pages = list()
    if urls:
        selected_page = random.choice(urls)
       notselected_pages = [url for url in urls if url != selected_page]
    return selected_page, notselected_pages


def kill_children(parent_pid):
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):
        try:
            child.kill()
        except putil.NoSuchProcess as ex:
            pass


def kill_all(parent_pid, signum, frame):
    """ kill geckodriver and firefox processes, finally kill current process""" 
    kill_children(parent_pid)
    parent = psutil.Process(parent_pid)
    parent.kill()

def main(page_visit_duration):
    # Set signal handler
    signal_handler_partial = partial(kill_all, os.getpid())
    signal.signal(signal.SIGTERM, signal_handler_partial)
    signal.signal(signal.SIGINT, signal_handler_partial)
    # Load config from config.yaml
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.yaml')) as stream:
        config = yaml.safe_load(stream)
    binary_path = config['driver']['binary_path']
    binary_type = config['driver']['binary_type']
    my_driver = init_driver(binary_path, binary_type)
    if my_driver is not None:
        # Init local variables
       qos_metrics_lists = dict()
       qos_metrics = dict()
       for metric in config['qos_metrics']:
           qos_metrics[metric] = config['qos_metrics'][metric]['js']
       web_pages_root = config['web_pages_to_fetch']
       # Randomly select a web page from which start navigation
       start_page = random.choice(web_pages_root)
       selected_page = start_page
       prev_notselected_pages = list()
       try:
           while True:
               s = "# Consulting web page " + selected_page + " #"
            print('\n' + s)
            timestamp = collect_agent.now()
            my_qos_metrics = compute_qos_metrics(my_driver, selected_page, qos_metrics)
            if not my_qos_metrics:
               selected_page = random.choice(web_pages_root)
               continue
            print_qos_metrics(my_qos_metrics, config)
            statistics = {'url':selected_page}
            for key, value in my_qos_metrics.items():
                statistics.update({key:value})
            collect_agent.send_stat(timestamp, **statistics)
            time.sleep(page_visit_duration)
            selected_page, notselected_pages = choose_page_to_visit(my_driver)
            # Handle pages with no clickable element
            if selected_page is None:
               if not prev_notselected_pages:
                  selected_page = random.choice(web_pages_root)
                  while selected_page == start_page:
                     selected_page = random.choice(web_pages_root)
                  start_page = selected_page
               else:
                  selected_page = random.choice(prev_notselected_pages)
                  notselected_pages = [page for page in prev_notselected_pages if page != selected_page]
            prev_notselected_pages = notselected_pages
       # Handle exceptions such as network timeout exception
       except Exception as ex:
              message = 'An unexpected exception occured: {}'.format(ex)
              collect_agent.send_log(syslog.LOG_ERR, message)
              print(message)
              exit(message)
       finally:
             # Kill children processes including geckodriver and firefox
             kill_children(os.getpid()) 
    else:
        message = 'Sorry, specified driver is not available. For now, only Firefox driver is supported'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/random_web_browsing_qoe/random_web_browsing_qoe_rstats_filter.conf'):
        # Argument parsing
        parser = argparse.ArgumentParser()
        parser.add_argument("page_visit_duration", help="The amount of time in second, spend on each web page once it is loaded", type=int)
        args = parser.parse_args()
        
        main(args.page_visit_duration)
