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


"""Sources of the Job netflix"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Francklin SIMO <francklin.simo@toulouse.viveris.com>
'''
import os
import sys
import time
import syslog
import argparse
import yaml
import collect_agent
import webbrowser
from selenium import webdriver 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

import random
import math


URL = "https://www.netflix.com/fr/" 


def connect_to_collect_agent():
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/netflix/'
            'netflix_rstats_filter.conf')
    if not success:
        message = 'Error connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    collect_agent.send_log(syslog.LOG_DEBUG, 'Starting job Netflix')

def handle_exception(netflix, message):
    collect_agent.send_log(syslog.LOG_ERR, message)
    print( message)
    netflix.close_browser()
    exit(message)
    
  
class Netflix:
    
    def __init__(self, email_address, password, timeout):
        self.email_address = email_address
        self.password = password
        self.timeout = timeout
        
    # TODO: Add support for other web browsers
    def open_browser(self):
        """
          Launch the browser and load the web page for login to skype                 
        """ 
        # Connect to collect agent
        connect_to_collect_agent
            
        # Initialize a Selenium driver. Only support googe-chrome for now.
        try:
            # Load config from config.yaml
            config = yaml.safe_load(open(os.path.join(os.path.abspath(
                    os.path.dirname(__file__)),
                    'config.yaml'))
            )
            binary_type =  config['driver']['binary_type']
            binary_path = config['driver']['binary_path']
            chromedriver_path = config['driver']['executable_path']
            if binary_type == "GoogleChromeBinary":
                chrome_options = Options()
                # Path to binary google-chrome 
                chrome_options.binary_location = binary_path
                # Runs Chrome in headless mode
                chrome_options.add_argument("--headless")
                self.driver = webdriver.Chrome(executable_path=chromedriver_path,
                                               chrome_options=chrome_options
                )
                #self.driver.maximize_window()
        except Exception as ex:
            message = 'ERROR when initializing the web driver: {}'.format(ex)
            handle_exception(self, message)
            
        
        # Launch the browser and load login page
        try:
            self.driver.delete_all_cookies()
            self.driver.get(URL)
            self.persistent_wait = WebDriverWait(self.driver, math.inf)
            self.wait = WebDriverWait(self.driver, self.timeout)
            self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "S'identifier")))
             
         # Catch: WebDriveException, InvalideSelectorExeception, NoSuchElementException, TimeoutException
        except Exception as ex:
            message = 'ERROR when launching the browser: {}'.format(ex)
            handle_exception(self, message)
            
    def login(self):
        """
          Sign in to user netflix account using specified email_address and password 
          and choose the first profile                 
        """ 
        try:
            element = self.driver.find_element_by_link_text("S'identifier")
            self.driver.execute_script("arguments[0].click();", element)
            self.wait.until(EC.presence_of_element_located((By.ID, "id_userLoginId")))
            self.wait.until(EC.presence_of_element_located((By.ID, "id_password")))
            self.driver.find_element_by_id("id_userLoginId").clear()
            self.driver.find_element_by_id("id_userLoginId").send_keys(self.email_address)
            self.driver.find_element_by_id("id_password").clear()
            self.driver.find_element_by_id("id_password").send_keys(self.password)
            # Click on the button "Sign in"
            self.driver.find_element_by_xpath("//button[@type='submit']").click()
            self.wait.until(EC.presence_of_element_located((
                    By.XPATH,
                    '//*[@id="appMountPoint"]/div/div/div/div/div[2]/div/div/ul/li[1]/div/a',
            )))
            self.driver.find_element_by_xpath(
                    '//*[@id="appMountPoint"]/div/div/div/div/div[2]/div/div/ul/li[1]/div/a'
            ).click()
        # Catch: WebDriveException, InvalideSelectorExeception, NoSuchElementException
        except Exception as ex:
            message = 'ERROR when login: {}'.format(ex)
            handle_exception(self, message)
    
    def search_video(self):
        """
        Find videos by a keyword witch is choosen from a predefined list and wait until video 
        is ready to play
        """
        # Load config from config.yaml
        self.config = yaml.safe_load(open(os.path.join(os.path.abspath(
                os.path.dirname(__file__)),
                'config.yaml'))
        )
        # Randomly select a keyword
        keyword = random.choice(self.config['keywords'])
        try:
            self.driver.find_element_by_xpath(
                    '//*[@id="appMountPoint"]/div/div/div[1]/div/div[1]/div/div/div/div[1]/div/button'
            ).click()
        
            self.driver.find_element(By.CSS_SELECTOR, ("input")).clear()
            self.driver.find_element(By.CSS_SELECTOR, ("input")).send_keys(keyword)
            self.wait.until(EC.presence_of_element_located((
                        By.XPATH,
                        '//*[@id="title-card-0-0"]/div[1]/a/div'
            )))
            
        # Catch: TimeoutException, WebDriveException, InvalideSelectorExeception, NoSuchElementException
        except Exception as ex:
            message = 'ERROR when searching video: {}'.format(ex)
            handle_exception(self, message)
    
    def watch_video(self, duration):
        """
        Watch the first video found during *duration* seconds
        """
        try:
            element = self.driver.find_element_by_xpath(
                    '//*[@id="title-card-0-0"]/div[1]/a/div'
            )
            self.driver.execute_script("arguments[0].click();", element)
                 
            resume = True
            # If play button is displayed
            try:
                element = self.wait.until(EC.presence_of_element_located((
                            By.XPATH,
                            #'//*[@id="pane-Overview"]/div/div/div/div[1]/div/div[3]/a/span'
                            '//*[@id="pane-Overview"]/div/div/div/div[1]/div/div[5]/a/span'
                )))
                self.driver.execute_script("arguments[0].click();", element)
                resume = False
            except:
                pass
            
            # If resume buttton is displayed rather than play button
            if resume:
                try:
                    element = self.wait.until(EC.presence_of_element_located((
                                By.XPATH,
                                #'//*[@id="pane-Overview"]/div/div/div/div[1]/div/div[4]/a/span'
                                '//*[@id="pane-Overview"]/div/div/div/div[1]/div/div[5]/a/span'
                    )))
                    self.driver.execute_script("arguments[0].click();", element)
                    #element.click()
                except Exception as ex:
                    message = 'ERROR when launching video resume: {}'.format(ex)
                    handle_exception(self, message)
            
            time.sleep(duration)
        # Catch: TimeoutException, WebDriveException, InvalideSelectorExeception, NoSuchElementException
        except Exception as ex:
            message = 'ERROR when watching video: {}'.format(ex)
            handle_exception(self, message)
   
    def close_browser(self):
         """ Close the browser if open """
         self.driver.close()

 
def launch(email_address, password, duration, timeout):
    netflix = Netflix(email_address, password, timeout)
    print('###### Open browser and load login page ############')
    netflix.open_browser()
    print('###### Login ############')
    netflix.login()
    print('###### Search video ############')
    netflix.search_video()
    print('###### Launch video ############')
    netflix.watch_video(duration)
    print('###### Close browser ############')
    netflix.close_browser()
   

if __name__ == "__main__":
    # Define usage
    parser = argparse.ArgumentParser(
        description='This script connects to netflix and plays a video using a web browser.', 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("email_address", type=str,
                        help='the email address to use to sign in'
    )
    parser.add_argument('password', type=str,
                        help='the password associated to email_address'
    )
    parser.add_argument("duration", type=int,
                        help='duration for watching the video, in seconds'
    )
    parser.add_argument('-t', '--timeout', type=int, default=10,
                        help='the waiting period until an expected event occurs, in seconds.' 
                        ' It is set depending of network congestion'
    ) 
    
    # Get args
    args = parser.parse_args()
    email_address = args.email_address
    password = args.password
    duration = args.duration
    timeout = args.timeout
    launch(email_address, password, duration, timeout)
