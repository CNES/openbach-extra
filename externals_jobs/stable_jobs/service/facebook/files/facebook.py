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


"""Sources of the Job facebook"""

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
from selenium.webdriver.chrome.options import Options
import random
import math

URL = "https://facebook.com"
    
class Facebook:
  
    def __init__(self, email_address, password, timeout):
        self.email_address = email_address
        self.password = password
        self.timeout = timeout
  
    # TODO: Add support for other web browsers
    def open_browser(self):
        """
          Launch the browser and fetch the web page for login to facebook                 
        """ 
        # Connect to collect agent
        conffile = '/opt/openbach/agent/jobs/facebook/facebook_rstats_filter.conf'
        success = collect_agent.register_collect(conffile)
        if not success:
            message = 'ERROR when connecting to collect-agent'
            collect_agent.send_log(syslog.LOG_ERR, message)
            exit(message)
            
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
                # Feeds a test pattern to getUserMedia() instead of live camera input
                chrome_options.add_argument("--use-fake-device-for-media-stream")
                # Avoids the need to grant camera/microphone permissions
                chrome_options.add_argument("--use-fake-ui-for-media-stream")
                # Feeds a Y4M test file to getUserMedia() instead of live camera input
                video = os.path.join(os.path.abspath(
                        os.path.dirname(__file__)), 
                        random.choice(config['video_to_play'])
                )
                audio = os.path.join(os.path.abspath(
                        os.path.dirname(__file__)), 
                        random.choice(config['audio_to_play'])
                )
                chrome_options.add_argument("--use-file-for-fake-video-capture={}".format(video))
                # Feeds a WAV test file to getUserMedia() instead of live audio input
                chrome_options.add_argument("--use-file-for-fake-audio-capture={}".format(audio))
                # Enable notifications
                chrome_options.add_argument("--disable-notifications")
                # Runs Chrome in headless mode
                chrome_options.add_argument("--headless")
                self.driver = webdriver.Chrome(executable_path=chromedriver_path,
                                               chrome_options=chrome_options
                )
              
        except Exception as ex:
            message = 'ERROR when initializing the web driver: {}'.format(ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            print(message)
            self.close_browser()
            exit(message)
        
        # Launch the browser and fetch the login web page
        try:
            self.driver.delete_all_cookies()
            self.driver.get(URL)
            self.persistent_wait = WebDriverWait(self.driver, math.inf)
            self.wait = WebDriverWait(self.driver, self.timeout)
            self.wait.until(EC.presence_of_element_located((By.ID, "email")))
         # Catch: WebDriveException, InvalideSelectorExeception, NoSuchElementException, TimeoutException
        except Exception as ex:
            message = 'ERROR when launching the browser: {}'.format(ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            print(message)
            self.close_browser()
            exit(message)
           
    def login_in_facebook(self):
        """
          Sign in to user facebook account using specified email_address and password                  
        """ 
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, ("input[type='email']"))
            element.clear()
            element.send_keys(self.email_address)
            element = self.driver.find_element(By.CSS_SELECTOR, ("input[type='password']"))
            element.clear()
            element.send_keys(self.password)
            # Click on the button "Connexion"
            self.driver.find_element(By.CSS_SELECTOR, ("input[type='submit']")).submit()
            # Wait for chat is clickable
            self.wait.until(EC.element_to_be_clickable((
                    By.NAME,
                    "mercurymessages"
            )))
        # Catch: WebDriveException, InvalideSelectorExeception, NoSuchElementException
        except Exception as ex:
            message = 'ERROR when login: {}'.format(ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            print(message)
            self.close_browser()
            sys.exit(message)
    
    def search_friend(self, friend_name):
        """
        Find friend by its name and make a call            
        """
        try:
            self.driver.find_element_by_name("mercurymessages").click()
            self.wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//*[@id='MercuryJewelFooter']/a[1]"
            )))
            self.driver.find_element_by_xpath("//*[@id='MercuryJewelFooter']/a[1]").click()
            element = self.wait.until(EC.visibility_of_element_located((
                    By.XPATH,
                    #"//*[@id='js_k']/div/div/div[1]/span[1]/label/input"
                    "//input[@placeholder='Rechercher dans Messenger']"
                   
            )))
            element.clear()
            # Launch search and wait
            element.send_keys(friend_name)
            time.sleep(5)
            element = self.wait.until(EC.visibility_of_element_located((By.XPATH, 
            #"//div[@class='_364g'][text()='{}']".format(friend_name))))
            "//span/span[text()='{}']".format(friend_name))))
            element.click()      
        except Exception as ex:
            message = "ERROR when finding friend '{}' : {}".format(friend_name, ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            print(message)
            self.close_browser()
            sys.exit(message)
         
    def call_friend(self, call_type):
        xpath = "//div[@data-testid='{}']"
        if call_type == 'video':
            xpath = xpath.format('startVideoCall')
        else:
            xpath = xpath.format('startVoiceCall')
        call_element = self.driver.find_element_by_xpath(xpath)
        try:
            call_element.click()
        except Exception as ex:
            message = "ERROR when calling friend '{}' : {}".format(friend_name, ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            print(message)
            self.close_browser()
            sys.exit(message)
        
    def end_call(self, call_duration):
        """
        End call after *call_duration*
        """
        time.sleep(call_duration)        
        try:
            end_call_element = self.driver.find_element_by_xpath("//*[@id='fbRTC/container']/div[2]/div/div[5]"
            "/div/div/div/div/div/footer/section/button[4]")
            end_call_element.click()
        except:
          pass
        
    def close_browser(self):  
        """ Close the browser if open """
        self.driver.close()
    
def call(email_address, password, call_type, timeout, friend_name, call_duration):
    """
    Scenario for audio or video call. Launch the browser, log in facebook using specified user parameters, 
    find the contact, make call and close the browser after *call_duration* seconds.
    """
    facebook = Facebook(email_address, password, timeout)
    print('########## Launch the browser and load login page #############')
    facebook.open_browser()
    print('########## Sign In  #############')
    facebook.login_in_facebook()
    print('########## Open Facebook Chat and Search the friend #############')
    time.sleep(2)
    facebook.search_friend(friend_name)
    print('########## Call friend #############')
    facebook.call_friend(call_type)
    facebook.end_call(call_duration)
    print('########## Call Ended #############')
    facebook.close_browser()
    
def receive(email_address, password, call_type, timeout):
    """
    Launch the browser, log in facebook and wait for incoming call.
    """
    # Connect to collect agent
    conffile = '/opt/openbach/agent/jobs/facebook/facebook_rstats_filter.conf'
    success = collect_agent.register_collect(conffile)
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)
    facebook = Facebook(email_address, password, timeout)
    print('########## Launch browser and download the login page #############')
    facebook.open_browser()
    print('########## Sign In  #############')
    facebook.login_in_facebook()
    print('########## Wait for incoming call #############')
    # Wait for incoming call
    answer_call_element = facebook.persistent_wait.until(EC.element_to_be_clickable((
            By.XPATH, 
            "//button[@data-testid='answerCallButton']"
    )))           
    # Answer and wait until the caller ends the call
    answer_call_element.click()
    print('########## Answer call #############')
    facebook.wait.until(EC.number_of_windows_to_be(2))
    window_before = facebook.driver.window_handles[0]
    window_after = facebook.driver.window_handles[1]
    facebook.driver.switch_to.window(window_after)
    facebook.wait.until(EC.presence_of_element_located((
            By.XPATH, 
            "//button[@data-testid='endCallButton']"
    )))
    facebook.persistent_wait.until_not(EC.presence_of_element_located((
            By.XPATH, 
            "//button[@data-testid='endCallButton']"
    )))
    facebook.driver.switch_to.window(window_before)
    print('########## call Ended #############')
    
    
if __name__ == "__main__":
    # Define usage
    parser = argparse.ArgumentParser(description='This script sign in to a facebook user account,'
            ' finds a friend by its username and makes a video or audio call.'
            ' It can also be run to receive a call.', 
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Caller or receiver arguments
    parser.add_argument("email_address", type=str,
                        help='The email address to use to sign in'
    )
    parser.add_argument('password', type=str,
                        help='The password associated to email_address'
    )
    parser.add_argument('call_type', choices=['audio', 'video'],
                        help='The type of call (audio or video)'
    )
    parser.add_argument('-t', '--timeout', type=int, default=10,
                        help='The waiting period until an expected event occurs, in seconds.' 
                        ' It is set depending of network congestion'
    ) 
    # Sub-commands functionnality to split 'caller' mode and 'receiver' mode
    subparsers = parser.add_subparsers(
            title='Subcommand mode',
            help='Choose the mode (caller mode or receiver mode)'
    )
    subparsers.required=True
    # Receiver specific arguments
    parser_receiver = subparsers.add_parser('receiver', help='Run in receiver mode')
    # Caller specific arguments
    parser_caller = subparsers.add_parser('caller', help='Run in caller mode')
    parser_caller.add_argument('friend_name', type=str,
                        help='The name of the friend to call'
    )
    parser_caller.add_argument('-d', '--call_duration', type=int, default=math.inf,
                        help='The duration of the call, in seconds'
    )
    # Set subparsers options to automatically call the right
    # Function depending on the chosen subcommand
    parser_receiver.set_defaults(function=receive)
    parser_caller.set_defaults(function=call)
    # Get args and call the appropriate function
    args = vars(parser.parse_args())
    main = args.pop('function')
    main(**args)
