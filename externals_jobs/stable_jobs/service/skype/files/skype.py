#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2023 CNES
# Copyright © 2022 Eutelsat
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
 * Bastien TAURAN <bastien.tauran@viveris.fr>
'''

import os
import math
import time
import psutil
import signal
import syslog
import random
import argparse
import subprocess
from functools import partial

import yaml
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import collect_agent


URL = "https://web.skype.com"


def kill_children(parent_pid):
    """ KIll all subprocesses including firefox and geckodriver"""
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):
        try:
           child.kill()
        except psutil.NoSuchProcess as ex:
           pass


def kill_all(parent_pid, signum, frame):
    """ Kill all children processes before killing parent process"""
    kill_children(parent_pid)
    parent = psutil.Process(parent_pid)
    parent.kill()


def set_signal_handler():
    signal_handler_partial = partial(kill_all, os.getpid())
    signal.signal(signal.SIGTERM, signal_handler_partial)
    signal.signal(signal.SIGINT, signal_handler_partial)


def check_exists_by_xpath(web_driver, xpath):
    try:
        web_driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


class Skype:
    def __init__(self, email_address, password, timeout):
        self.email_address = email_address
        self.password = password
        self.timeout = timeout

    # TODO: Add support for other web browsers
    def open_browser(self):
        """Launch the browser and fetch the web page for login to skype"""
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
                options = webdriver.ChromeOptions()
                # Path to binary google-chrome 
                options.binary_location = binary_path
                # Feeds a test pattern to getUserMedia() instead of live camera input
                options.add_argument("--use-fake-device-for-media-stream")
                # Avoids the need to grant camera/microphone permissions
                options.add_argument("--use-fake-ui-for-media-stream")
                # Feeds a Y4M test file to getUserMedia() instead of live camera input
                video = os.path.join(os.path.abspath(
                        os.path.dirname(__file__)),
                        random.choice(config['video_to_play'])
                )
                audio = os.path.join(os.path.abspath(
                        os.path.dirname(__file__)),
                        random.choice(config['audio_to_play'])
                )
                options.add_argument("--use-file-for-fake-video-capture={}".format(video))
                # Feeds a WAV test file to getUserMedia() instead of live audio input
                options.add_argument("--use-file-for-fake-audio-capture={}".format(audio))
                # To make elements visible in headless mode
                options.add_argument("window-size=1200,1100")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--allow-file-access-from-files")
                options.add_argument("--no-proxy")
                options.add_argument("--disable-default-apps")
                options.add_argument("--enable-crashpad")
                options.add_argument("--disable-setuid-sandbox")
                options.add_argument("--disable-background-networking")

                experimentalFlags = ['temporary-unexpire-flags-m100@1', 'enable-webrtc-hide-local-ips-with-mdns@2']
                chromeLocalStatePrefs = {'browser.enabled_labs_experiments': experimentalFlags}
                options.add_experimental_option('localState', chromeLocalStatePrefs)

                self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        except Exception as ex:
            collect_agent.send_log(syslog.LOG_ERR, 'ERROR when initializing the web driver')
            raise

        # Launch the browser and fetch the login web page
        try:
            self.driver.delete_all_cookies()
            self.driver.get(URL)
            self.persistent_wait = WebDriverWait(self.driver, math.inf)
            self.wait = WebDriverWait(self.driver, self.timeout)
            #self.wait.until(EC.presence_of_element_located((By.ID, "i0116")))
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
         # Catch: WebDriveException, InvalideSelectorExeception, NoSuchElementException, TimeoutException
        except Exception as ex:
            message = (
                    'ERROR when loading login page: {} '
                    'It is probably due to either no internet connection or {} '
                    'is unreachable'.format(ex, URL)
            )
            collect_agent.send_log(syslog.LOG_ERR, message)
            raise

    def login_in_skype(self):
        """Sign in to user skype account using specified email_address and password"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, ("input[type='email']"))
            element.clear()
            element.send_keys(self.email_address)
            # Click on the button "Next"
            self.driver.find_element(By.ID, "idSIButton9").click()
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
            element = self.driver.find_element(By.CSS_SELECTOR, ("input[type='password']"))
            element.clear()
            element.send_keys(self.password)
            # Click on the button "Sign in"
            time.sleep(1)
            self.driver.find_element(By.CSS_SELECTOR, ("input[type='submit']")).submit()
            time.sleep(1)
            self.driver.find_element(By.CSS_SELECTOR, ("input[value='Yes']")).submit()
            time.sleep(1)
            self.wait.until(EC.visibility_of_element_located((
                    By.XPATH,
                    "//button[@title='People, groups, messages']"))
            )
        # Catch: WebDriveException, InvalideSelectorExeception, NoSuchElementException
        except Exception as ex:
            collect_agent.send_log(syslog.LOG_ERR, 'ERROR when login')
            raise

    def search_contact(self, contact_name):
        """Find the person to contact by its name from contacts list"""
        try:
            # Wait for contact refresh
            time.sleep(10)
            # Launch search
            element = self.wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[@title='People, groups, messages']/div"))
            )
            self.driver.execute_script("arguments[0].click();", element)
            self.wait.until(EC.visibility_of_element_located((
                    By.XPATH,
                    "//input[@placeholder='Search Skype']"))
            )
            search_element = self.driver.find_element(By.XPATH, "//input[@placeholder='Search Skype']")
            search_element.clear()
            search_element.send_keys(contact_name)
            # Wait for first contact is clickable then open conversation
            self.wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    ".//*[contains(@aria-label, '{}')]".format(contact_name)))
            ).click()
        except Exception as ex:
            collect_agent.send_log(syslog.LOG_ERR, 'ERROR when finding contact {}'.format(contact_name))
            raise

    def call_person(self, contact_name, call_type, call_duration):
        """ Launch *call_type* call and stop communication after *call_duration* seconds"""
        xpath = "//button[@title='{}']"
        try:
            if call_type == 'video':
                xpath = xpath.format('Video Call')
            else:
                xpath = xpath.format('Audio Call')
            call_element = self.driver.find_element(By.XPATH, xpath)
        except Exception as ex:
            collect_agent.send_log(syslog.LOG_ERR, 'ERROR when launching call')
            raise

        try:
            #Select Skype call if the contact can be reachable by another way such as via its mobile number
            call_element = self.driver.find_element(By.XPATH, "/html/body/ul/li[1]")
        except:
            pass
        finally:
            call_element.click()
            xpath = "//button[@aria-label='End Call']"
            self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            while check_exists_by_xpath(self.driver, xpath) and call_duration > 0:
                time.sleep(1)
                call_duration -= 1
            if call_duration != 0:
                message = '{} is not available'.format(contact_name)
                collect_agent.send_log(syslog.LOG_ERR, message)
                sys.exit(message)

    def end_call(self):
        """End the communication"""
        try:
            end_call_element = self.driver.find_element(By.XPATH, "//button[@aria-label='End Call']")
            end_call_element.click()
        except:
            pass

    def close_browser(self):
        """Close the browser if open"""
        self.driver.close()


def call(email_address, password, call_type, timeout, contact_name, call_duration):
    """
    Launch the browser, login in skype using specified user parameters,
    find the contact, make call and close the browser after *call_duration* seconds.
    """
    os.environ["DISPLAY"] = ":1"
    # Set signal handler
    set_signal_handler()
    p = subprocess.Popen(['Xvfb', ':1', '-screen', '0', '1024x768x16'])
    try:
        skype = Skype(email_address, password, timeout)
        print('########## Launch the browser and fetch login page #############')
        skype.open_browser()
        print('########## Sign In  #############')
        skype.login_in_skype()
        print('########## Find the contact #############')
        time.sleep(2)
        skype.search_contact(contact_name)
        # Wait for DOM to refresh
        time.sleep(5)
        print('########## Start Call #############')
        skype.call_person(contact_name, call_type, call_duration)
        skype.end_call()
        print('########## Call Ended #############')
        skype.close_browser()
    finally:
        p.terminate()
        kill_children(os.getpid())


def receive(email_address, password, call_type, timeout):
    """
    Launch the browser, login in skype, and wait for incoming call.
    """
    os.environ["DISPLAY"] = ":1"
    set_signal_handler()
    p = subprocess.Popen(['Xvfb', ':1', '-screen', '0', '1024x768x16'])
    try:
        skype = Skype(email_address, password, timeout)
        print('########## Launch the browser and fetch login page #############')
        skype.open_browser()
        print('########## Sign In  #############')
        skype.login_in_skype()
        print('########## Wait for incoming call #############')
        # Wait for incoming call
        if call_type == 'audio':
            answer_call_element = skype.persistent_wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(@aria-label, 'Answer call') and contains(@aria-label, 'voice only')]"))
            )
        else:
            answer_call_element = skype.persistent_wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(@aria-label, 'Answer call') and contains(@aria-label, 'video')]"))
            )
        time.sleep(2)
        answer_call_element.click()
        skype.persistent_wait.until(EC.presence_of_element_located((
               By.XPATH,
               "//button[@aria-label='End Call']",
        )))
        skype.persistent_wait.until_not(EC.presence_of_element_located((
               By.XPATH,
               "//button[@aria-label='End Call']",
        )))
        skype.close_browser()
        print('########## call Ended #############')
    finally:
        p.terminate()
        kill_children(os.getpid())


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/skype/skype_rstats_filter.conf'):
        # Define usage
        parser = argparse.ArgumentParser(
                description='This script sign in to a skype user account,'
                ' finds a contact by its name and makes a video or audio '
                'call. It can also be run to answer a call',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        # Caller or receiver arguments
        parser.add_argument("email_address", help='The email address to use to sign in')
        parser.add_argument('password', help='The password associated to email_address')
        parser.add_argument(
                'call_type', choices=['audio', 'video'],
                help='The type of call (audio or video)')
        parser.add_argument(
                '-t', '--timeout',
                type=int, default=10,
                help='The waiting period until an expected event occurs, '
                'in seconds. It is set depending of network congestion')

        # Sub-commands functionnality to split 'caller' mode and 'receiver' mode
        subparsers = parser.add_subparsers(
                title='Subcommand mode',
                help='Choose the skype mode (caller mode or receiver mode)')
        subparsers.required=True

        # Receiver specific arguments
        parser_receiver = subparsers.add_parser('receiver', help='Run in receiver mode')
        # Caller specific arguments
        parser_caller = subparsers.add_parser('caller', help='Run in caller mode')
        parser_caller.add_argument('contact_name', help='The name of the contact to call')
        parser_caller.add_argument(
                '-d', '--call_duration',
                type=int, default=120,
                help='The duration of the call, in seconds')

        # Set subparsers options to automatically call the right
        # Function depending on the chosen subcommand
        parser_receiver.set_defaults(function=receive)
        parser_caller.set_defaults(function=call)

        # Get args and call the appropriate function
        args = vars(parser.parse_args())
        main = args.pop('function')
        main(**args)
