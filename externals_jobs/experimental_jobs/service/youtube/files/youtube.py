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


"""Sources of the Job youtube"""

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
from urllib.request import urlopen
from urllib.request import quote
from bs4 import BeautifulSoup
import random

SEARCH_URL = "https://www.youtube.com/results?search_query="
WATCH_URL = 'https://www.youtube.com' 
  
class Youtube:
  
    def search_video(self):
        """
        Find videos by a keyword witch is choosen from a predefined list and keep url 
        for watching proposed videos    
        """
        # Connect to collect agent
        conffile = '/opt/openbach/agent/jobs/youtube/youtube_rstats_filter.conf'
        success = collect_agent.register_collect(conffile)
        if not success:
            message = 'ERROR when connecting to collect-agent'
            collect_agent.send_log(syslog.LOG_ERR, message)
            exit(message)
        # Load config from config.yaml
        self.config = yaml.safe_load(open(os.path.join(os.path.abspath(
                os.path.dirname(__file__)),
                'config.yaml'))
        )
        self.keyword = random.choice(self.config['keywords'])
        self.query = quote(self.keyword)
        self.response = urlopen(SEARCH_URL + self.query )
        html = self.response.read()
        soup = BeautifulSoup(html,"lxml")
        self.results=[]
        for video in soup.findAll(attrs={'class':'yt-uix-tile-link'}):
        	self.link=video['href']
        	if self.link[0:6]=='/watch':
        		self.results.append(WATCH_URL + video['href'])
        time.sleep(10)
   
    def watch_video(self, duration):
        """
          Launch the browser and play a randomly selected video from the list of proposed video,
          during *duration* seconds                 
        """ 
        # Initialize a Selenium driver. Only support googe-chrome for now.
        try:
            binary_type =  self.config['driver']['binary_type']
            binary_path = self.config['driver']['binary_path']
            chromedriver_path = self.config['driver']['executable_path']
            if binary_type == "GoogleChromeBinary":
                chrome_options = Options()
                # Path to binary google-chrome 
                chrome_options.binary_location = binary_path
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
        
        # Launch the browser and play video during *duration* seconds
        try: 
            self.driver.delete_all_cookies()
            url = random.choice(self.results)
            self.driver.get(url)
            time.sleep(duration)
        except Exception as ex:
            message = 'ERROR when watching video: {}'
            collect_agent.send_log(syslog.LOG_ERR, message.format(ex))
            print( message.format(ex))
            self.close_browser()
            exit(message)
   
    def close_browser(self):
         """ Close the browser if open """
         self.driver.close()

 
def launch(duration):
    youtube = Youtube()
    youtube.search_video()
    youtube.watch_video(duration)
    youtube.close_browser()
   

if __name__ == "__main__":
    # Define usage
    parser = argparse.ArgumentParser(
        description='This script finds youtube videos by a randomly'
                    ' selected keyword then plays a randomly selected video using a web browser.', 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('duration', type=int,
                        help='The duration for watching the video, in seconds'
    )
    
    # Get args
    args = parser.parse_args()
    launch(args.duration)
