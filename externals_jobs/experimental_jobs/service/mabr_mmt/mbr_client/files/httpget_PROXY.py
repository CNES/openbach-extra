#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author:  / <@toulouse.viveris.com>

"""
httpget_local.py - <+description+>
"""

import os
import re
import sys
import stat
import time
import shutil
import syslog
import signal
import argparse
import requests
import subprocess
from threading import Thread
from functools import total_ordering

import iptc
import collect_agent

DEFAULT_FIRST = -1
N_FILES_MIN = 50
RESOLUTION_PATTERN = re.compile(r'<Representation(?:.+)bandwidth="([0-9]+)"')

@total_ordering
class Element(object):
    """
    An element is defined by:
    - a filename
    - a flag indicating if it was sent
    """

    def __init__(self, file_num, sent):
        self.file_num = file_num
        self.sent = sent

    def _get_file_num(self):
        return self.file_num

    def _get_sent(self):
        return self.sent

    def _set_file_num(self, file_num):
        self.file_num = file_num

    def _set_sent(self, sent):
        self.sent = sent

    def __eq__(self, other):
        if hasattr(other, 'file_num'):
            return self.file_num.__eq__(other.file_num)

    def __lt__(self, other):
        if hasattr(other, 'file_num'):
            return self.file_num.__lt__(other.file_num)

class HttpGetProxy(object):
    def __init__(
            self, mm, rx_dir, mpd_dir, proxy, server_ip,
            resolutions, content_name, content_name_short,
            segment_duration, first_seg=DEFAULT_FIRST):
        # Conf variables
        self._mm = mm
        self._first_seg = first_seg
        self._rx_dir = rx_dir
        self._mpd_dir = mpd_dir
        self._proxy = proxy
        self._server_ip = server_ip
        self._resolutions = resolutions
        self._content_name = content_name
        self._content_name_short = content_name_short
        self._segment_duration = segment_duration
        # Status variables
        self._elements = []
        self._mp4_file = None
        self._mpd_file = None
        self._iptc_rule = None
        self._iptc_chain = None
        # Thread variables
        self._shutdown = False
        self._thread = Thread(target=self._run)

    def start(self):
        """ Start execution """
        self._thread.start()

    def wait(self, timeout=None):
        """ Wait on thread """
        if self._thread:
            self._thread.join(timeout)

    def stop(self):
        """ Stop thread """
        self._shutdown = True

        # Remove rule iptables
        if self._iptc_rule:
            self._iptc_chain.delete_rule(self._iptc_rule)

        self.wait(1)

    def _new_elements(self):
        """ Search for new elements on the rx directory """
        new = False
        for root, dirs, files in os.walk(self._rx_dir, topdown=True):
            # Wait if we don't have a minimum number of files
            if len(files) < N_FILES_MIN:
                time.sleep(0.2)
            # Create a new element for each segment
            for filename in files:
                if filename.endswith('.mpd'):
                    number = -1
                    self._mpd_file = filename
                elif filename.endswith('.mp4'):
                    number = 0
                    self._mp4_file = filename
                else:
                    try:
                        number = int(re.findall('([0-9]+)\.m4s', filename)[0])
                    except IndexError:
                        continue
                if 0 < int(number) and int(number) < self._first_seg:
                    continue
                # Check if element exists, else add to list
                new_element = Element(number, False)
                if new_element not in self._elements:
                    self._elements.append(new_element)
                    new = True
        return new

    def _send_mpd_file(self, elt):
        """" Send the mpd file """
        if self._mm:
            self._resolutions = set()
            with open(os.path.join(self._rx_dir, self._mpd_file)) as openfile:
                contents = openfile.read()
                self._resolutions.update(re.findall(RESOLUTION_PATTERN, contents))
                
        collect_agent.send_log(syslog.LOG_DEBUG, "RESOLUTIONS: {}".format(self._resolutions))

        filename = self._mpd_file # TODO: should search instead?
        origin = os.path.join(self._rx_dir,filename)
        destination = self._mpd_dir
        subprocess.call("sudo cp {} {}".format(origin,destination),shell=True)
        os.chmod(os.path.join(self._mpd_dir, filename), 0o644)
        url = 'http://{}/vod-dash/{}/{}sec/{}'.format(
                self._server_ip, self._content_name,
                self._segment_duration, filename)
        response = None
        while not response or requests.get(url, proxies=self._proxy).status_code != 200:
            response = requests.get(url, proxies=self._proxy)
            collect_agent.send_log(syslog.LOG_DEBUG, 'Response {}_{}s.mpd: {}'.format(
                    self._content_name, self._segment_duration, 
                    response.status_code))
            if response.status_code == 403 :
                subprocess.run(['conntrack', '-F'])
        elt.sent = True

    def _send_mp4_file(self, elt):
        """" Send the mp4 file """
        for res in self._resolutions:
            filename = self._mp4_file # TODO: should search instead?
            origin = os.path.join(self._rx_dir,filename)
            destination = os.path.join(self._mpd_dir,'{}_{}bps/'.format(self._content_name_short,res))
            subprocess.call("sudo cp {} {}".format(origin,destination),shell=True)
            os.chmod(os.path.join(self._mpd_dir, '{}_{}bps/'.format(
                    self._content_name_short, res), filename), 0o644)
            url = 'http://{}/vod-dash/{}/{}sec/{}_{}bps/{}'.format(
                    self._server_ip, self._content_name, self._segment_duration,
                    self._content_name_short, res, filename)
            response = None
            while not response or (response.status_code != 200 and response.status_code != 404):
                response = requests.get(url, proxies=self._proxy)
                collect_agent.send_log(syslog.LOG_DEBUG, 'Response {}_{}s.mp4 <{}> : {}'.format(
                        self._content_name, self._segment_duration, 
                        res, response.status_code))
                if response.status_code == 403 :
                    subprocess.run(['conntrack', '-F'])
            if response.status_code == 200:
                elt.sent=True

    def _send_m4s_file(self, elt):
        """" Send a m4s file """
        for res in self._resolutions:
            filename="{}_{}s{}.m4s".format(
                self._content_name, self._segment_duration, elt.file_num)
            origin = os.path.join(self._rx_dir,filename)
            destination = os.path.join(self._mpd_dir,'{}_{}bps/'.format(self._content_name_short,res))
            subprocess.call("sudo cp {} {}".format(origin,destination),shell=True)
            os.chmod(os.path.join(self._mpd_dir, '{}_{}bps/'.format(
                    self._content_name_short, res), filename), 0o644)
            url = 'http://{}/vod-dash/{}/{}sec/{}_{}bps/{}'.format(
                    self._server_ip, self._content_name,
                    self._segment_duration, self._content_name_short,
                    res, filename)
            response = None
            
            while not response or (response.status_code != 200 and
                                   response.status_code != 404):
                response = requests.get(url, proxies=self._proxy)
                collect_agent.send_log(syslog.LOG_DEBUG, 'Response {}_{}s{}.m4s <{}> : {}'.format(
                        self._content_name, self._segment_duration,
                        elt.file_num, res, response.status_code))
                if response.status_code == 403 :
                    subprocess.run(['conntrack', '-F'])
            if response.status_code == 200:
                elt.sent=True

    def _run(self):
        """ Thread function """
        while not self._shutdown:
            if not self._new_elements():
                continue

            # Sort elements
            self._elements.sort()

            # Consider only elements that have not been sent
            for elt in filter(lambda x: not x.sent, self._elements):
                if(elt.file_num == -1):
                    path = os.path.join(self._rx_dir, self._mpd_file)
                elif (elt.file_num == 0):
                    path = os.path.join(self._rx_dir, self._mp4_file)
                else:
                    path = os.path.join(self._rx_dir,
                            "{}_{}s{}.m4s".format(
                                    self._content_name, self._segment_duration,
                                    elt.file_num))

                # Wait until file is released ...
                while (os.stat(path).st_mode & (stat.S_IXGRP | stat.S_ISGID) == stat.S_ISGID):
                    pass
                # MPD file
                if (elt.file_num == -1):
                    self._send_mpd_file(elt)
                # MP4 file
                elif (elt.file_num == 0):
                    self._send_mp4_file(elt)
                # M4S file
                else:
                    self._send_m4s_file(elt)

if __name__ == "__main__":
    def proxy_type(arg):
        return { arg.split(':')[0] : ':'.join(arg.split(':')[1:]) }

    def comma_separated_list(arg):
        return set(map(str.strip, arg.split(',')))

    # Define usage
    parser = argparse.ArgumentParser(
            description='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            '--mm', action='store_true', help='Use multicast from the beginning')
    parser.add_argument(
            '--first-seg', type=int,
            help='The first segment number to start the requests (default: {})'.format(DEFAULT_FIRST))
    parser.add_argument('rx_dir', type=str, help='The Norm Rx directory')
    parser.add_argument('mpd_dir', type=str, help='The mpd directory')
    parser.add_argument('proxy', type=proxy_type, help='The Squid url')
    parser.add_argument('server_ip', type=str, help='The server IP')
    parser.add_argument('content_name', type=str, help='The content name')
    parser.add_argument('content_name_short', type=str, help='The short content name')
    parser.add_argument('segment_duration', type=int, help='The content segment duration')
    parser.add_argument(
            '--resolutions', type=comma_separated_list, 
            default={1546902, 334349, 4219897, 45652},
            help='The contents resolutions')

    # Get arguments
    args = parser.parse_args()

    kwargs = { 
            key: val for key, val in vars(args).items 
            if val is not None and key in {'first_seg'} }

    conffile = '/opt/openbach/agent/jobs/twinkle_voip/mbr_client_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    proxy = HttpGetProxy(
            args.mm, args.rx_dir, args.mpd_dir, args.proxy,
            args.server_ip, args.resolutions, args.content_name,
            args.content_name_short, args.segment_duration, **kwargs)
    proxy.start()

    def stop_wrapper(sig_number, stack_frame):
        proxy.stop()

    signal.signal(signal.SIGINT, stop_wrapper)
    signal.signal(signal.SIGTERM, stop_wrapper)

    try:
        proxy.wait()
    except KeyboardInterrupt:
        proxy.stop()
