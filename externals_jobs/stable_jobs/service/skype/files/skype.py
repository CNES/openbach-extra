
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


"""Sources of the Job skype"""

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

URL = "https://web.skype.com/fr/"
    
class Skype:
  
    def __init__(self, email_address, password, timeout):
        self.email_address = email_address
        self.password = password
        self.timeout = timeout
  
    # TODO: Add support for other web browsers
    def open_browser(self):
        """
          Launch the browser and fetch the web page for login to skype                 
        """ 
        # Connect to collect agent
        conffile = '/opt/openbach/agent/jobs/skype/skype_rstats_filter.conf'
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
                # Runs Chrome in headless mode
                chrome_options.add_argument("--headless")
                self.driver = webdriver.Chrome(executable_path=chromedriver_path,
                                               chrome_options=chrome_options
                )
        except Exception as ex:
            message = 'ERROR when initializing the web driver: {}'
            collect_agent.send_log(syslog.LOG_ERR, message.format(ex))
            print( message.format(ex))
            self.close_browser()
            exit(message)
        
        # Launch the browser and fetch the login web page
        try:
            self.driver.delete_all_cookies()
            self.driver.get(URL)
            self.persistent_wait = WebDriverWait(self.driver, math.inf)
            self.wait = WebDriverWait(self.driver, self.timeout)
            self.wait.until(EC.presence_of_element_located((By.ID, "i0116")))
         # Catch: WebDriveException, InvalideSelectorExeception, NoSuchElementException, TimeoutException
        except Exception as ex:
            message = 'ERROR when launching the browser: {}'
            collect_agent.send_log(syslog.LOG_ERR, message.format(ex))
            print( message.format(ex))
            self.close_browser()
            exit(message)
           
    def login_in_skype(self):
        """
          Sign in to user skype account using specified email_address and password                  
        """ 
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, ("input[type='email']"))
            element.clear()
            element.send_keys(self.email_address)
            # Click on the button "Next"
            self.driver.find_element_by_id("idSIButton9").click()
            time.sleep(2)
            element = self.driver.find_element(By.CSS_SELECTOR, ("input[type='password']"))
            element.clear()
            element.send_keys(self.password)
            # Click on the button "Sign in"
            self.driver.find_element(By.CSS_SELECTOR, ("input[type='submit']")).submit()
            self.wait.until(EC.visibility_of_element_located((
                                  By.XPATH,
                                  "//button[@title='People, groups & messages']"))
            )
        # Catch: WebDriveException, InvalideSelectorExeception, NoSuchElementException
        except Exception as ex:
            message = 'ERROR when login: {}'.format(ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            print(message)
            self.close_browser()
            sys.exit(message)
    
    def search_contact(self, contact_name):
        """
        Find the person to contact by its name from contacts list             
        """
        try:
            # Launch search
            element = self.wait.until(EC.element_to_be_clickable((
                                  By.XPATH,
                                  "//button[@title='People, groups & messages']/div"))
            )
            self.driver.execute_script("arguments[0].click();", element)
            #self.driver.find_element_by_xpath("//button[@title='People, groups & messages']/div").click()
            self.wait.until(EC.visibility_of_element_located((
                                  By.XPATH,
                                  "//input[@placeholder='Search Skype']"))
            )
            search_element = self.driver.find_element_by_xpath("//input[@placeholder='Search Skype']")
            search_element.clear()
            search_element.send_keys(contact_name)
            # Wait for first contact is clickable then open conversation
            self.wait.until(EC.element_to_be_clickable((
                                  By.XPATH,
                                  "//div[@role='group'][@aria-label='PEOPLE']/div[2]"))
            ).click()
        except Exception as ex:
            message = 'ERROR when finding contact {} : {}'.format(contact_name, ex)
            collect_agent.send_log(syslog.LOG_ERR, message)
            print(message)
            self.close_browser()
            sys.exit(message)
         
    def call_person(self, call_type):
        if call_type == 'video':
            xpath = "//button[@title='Video Call']"
        else:
            xpath = "//button[@title='Audio Call']"
        call_element = self.driver.find_element_by_xpath(xpath)
        try:
            #Select Skype call if the contact can be reachable by another way such as via its mobile number
            call_element = self.driver.find_element_by_xpath("/html/body/ul/li[1]")
        except:
          pass
        finally:
          call_element.click()
           
    def end_call(self, call_duration):
        """
        End call after *call_duration*
        """
        time.sleep(call_duration)        
        try:
            end_call_element = self.driver.find_element_by_xpath("//button[@title='End Call']")
            end_call_element.click()
        except:
          pass
        
    def close_browser(self):  
        """ Close the browser if open """
        self.driver.close()
    
def call(email_address, password, call_type, timeout, contact_name, call_duration):
    """
    Scenario for audio or video call. Launch the browser, login in skype using specified user parameters, 
    find the contact, make call and close the browser after *call_duration* seconds.
    """
    skype = Skype(email_address, password, timeout)
    print('########## Launch the browser and load login page #############')
    skype.open_browser()
    print('########## Sign In  #############')
    skype.login_in_skype()
    print('########## Search the contact #############')
    time.sleep(2)
    skype.search_contact(contact_name)
    # Wait for DOM to refresh
    time.sleep(5)
    print('########## Call person #############')
    skype.call_person(call_type)
    skype.end_call(call_duration)
    print('########## Call Ended #############')
    skype.close_browser()
    
def receive(email_address, password, call_type, timeout):
    """
    Scenario for receiveing audio or video calling. Launch the browser, login in skype, 
    and wait for incoming call.
    """
    # Connect to collect agent
    conffile = '/opt/openbach/agent/jobs/skype/skype_rstats_filter.conf'
    success = collect_agent.register_collect(conffile)
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)
    skype = Skype(email_address, password, timeout)
    print('########## Launch the browser and load login page #############')
    skype.open_browser()
    print('########## Sign In  #############')
    skype.login_in_skype()
    print('########## Wait for incoming call #############')
    # Wait for incoming call
    if call_type == 'audio':
        answer_call_element = skype.persistent_wait.until(EC.presence_of_element_located((
                                      By.XPATH, 
                                      "//button[contains(@title, 'Answer call') "
                                      "and contains(@title, 'voice only')]"))
                              )
    else:
        answer_call_element = skype.persistent_wait.until(EC.presence_of_element_located((
                                      By.XPATH, 
                                      "//button[contains(@title, 'Answer call') " 
                                      "and contains(@title, 'video')]"))
                              )
    # Answer and wait until the caller end the call
    time.sleep(2)
    answer_call_element.click()
    skype.persistent_wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//button[@title='End Call']",
    )))
    skype.persistent_wait.until_not(EC.presence_of_element_located((
            By.XPATH, 
            "//button[@title='End Call']",
    )))
    #skype.close_browser()
    print('########## call Ended #############')
    
    
if __name__ == "__main__":
    # Define usage
    parser = argparse.ArgumentParser(description='This script sign in to a skype user account,'
            ' finds a contact by its name and makes a video or audio call. It can also be run to answer a call', 
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
            help='Choose the skype mode (caller mode or receiver mode)'
    )
    subparsers.required=True
    # Receiver specific arguments
    parser_receiver = subparsers.add_parser('receiver', help='Run in receiver mode')
    # Caller specific arguments
    parser_caller = subparsers.add_parser('caller', help='Run in caller mode')
    parser_caller.add_argument('contact_name', type=str,
                        help='The name of the contact to call'
    )
    parser_caller.add_argument('-d', '--call_duration', type=int, default=120,
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
