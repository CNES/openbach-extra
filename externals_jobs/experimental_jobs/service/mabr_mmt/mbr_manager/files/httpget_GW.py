#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author:  / <@toulouse.viveris.com>

"""
httpget_local.py - <+description+>
"""

import re
import os
import sys
import time
import signal
import syslog
import argparse
import requests
from threading import Thread

import collect_agent

DEFAULT_RESOLUTION = 4219897
DEFAULT_FIRST = 1
DEFAULT_LAST = 300

class HttpGetGw(object):

    def __init__(self, proxy, server_ip, content_name, content_name_short,
            segment_duration, mpd_file, mp4_file, resolution=DEFAULT_RESOLUTION,
            first_seg=DEFAULT_FIRST, last_seg=DEFAULT_LAST):
        # Conf variables
        self._proxy = proxy
        self._server_ip = server_ip
        self._first_seg = first_seg
        self._last_seg = last_seg
        self._resolution = resolution
        self._content_name = content_name
        self._segment_duration = segment_duration
        self._content_name_short = content_name_short
        self._mpd_file = mpd_file
        self._mp4_file = mp4_file
        # Thread variables
        self._shutdown = False
        self._main_t = Thread(target=self._main)

    def start(self):
        """ Start main thread """
        self._main_t.start()

    def wait(self, timeout=None):
        """ Wait for main thread to finish """
        self._main_t.join(timeout)

    def stop(self):
        """ Stop """
        self._shutdown = True
        self.wait(1)

    def _main(self):
        """ Main for main thread """
        # Request mpd file
        url = 'http://{}/vod-dash/{}/{}sec/{}'.format(
                self._server_ip, self._content_name, self._segment_duration, self._mpd_file)
        response = requests.get(url, proxies=self._proxy)
        collect_agent.send_log(syslog.LOG_DEBUG, 'HTTP_GET: {} : {}'.format(self._mpd_file, response.status_code))

        # Request mp4 file
        url = 'http://{}/vod-dash/{}/{}sec/{}_{}bps/{}'.format(
                self._server_ip, self._content_name, self._segment_duration,
                self._content_name_short, self._resolution, self._mp4_file)
        response = requests.get(url, proxies=self._proxy)
        collect_agent.send_log(syslog.LOG_DEBUG, 'HTTP_GET: {} <{}> : {}'.format(self._mp4_file, self._resolution,
                response.status_code))

        # Request m4s files
        for n in range(self._first_seg, self._last_seg):
            if self._shutdown:
                return
 
            url = 'http://{}/vod-dash/{}/{}sec/{}_{}bps/{}_{}s{}.m4s'.format(
                    self._server_ip, self._content_name, self._segment_duration,
                    self._content_name_short, self._resolution, 
                    self._content_name, self._segment_duration, n)
            response = requests.get(url, proxies=self._proxy)
            collect_agent.send_log(syslog.LOG_DEBUG, 'HTTP_GET: {}_{}s{}.m4s <{}> : {}'.format(
                self._content_name, self._segment_duration,
                n, self._resolution, response.status_code))


if __name__ == "__main__":
    def proxy_type(arg):
        return { arg.split(':')[0] : ''.join(arg.split(':')[1:]) }

    # Define usage
    parser = argparse.ArgumentParser(
            description='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            '--resolution', type=int,
            help='The resolution to request to the server (default: %i)'.format(DEFAULT_RESOLUTION))
    parser.add_argument(
            '--first-seg', type=int,
            help='The first segment number to start the requests (default: %i)'.format(DEFAULT_FIRST))
    parser.add_argument(
            '--last-seg', type=int,
            help='The last segment number to start the requests (default: %i)'.format(DEFAULT_LAST))
    parser.add_argument('server_ip', type=str, help='The server IP')
    parser.add_argument('proxy', type=proxy_type, help='The url of the proxy')
    parser.add_argument('content_name', type=str, help='The content name')
    parser.add_argument('content_name_short', type=str, help='The short content name')
    parser.add_argument('segment_duration', type=int, help='The segment duration')
    parser.add_argument('mpd_file', type=str, help='The mpd file path')
    parser.add_argument('mp4_file', type=str, help='The mp4 file path')

    args = parser.parse_args()
    opt_args = { var: value for var, value in vars(args).items() 
            if var in {'resolution', 'first_seg', 'last_seg'} 
            and value is not None }

    conffile = '/opt/openbach/agent/jobs/twinkle_voip/mbr_manager_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    proxy = HttpGetGw(
            args.proxy, args.server_ip, args.content_name, args.content_name_short,
            args.segment_duration, args.mpd_file, args.mp4_file, **opt_args)
    proxy.start()

    def stop_wrapper(sig_number, stack_frame):
        proxy.stop()                

    signal.signal(signal.SIGINT, stop_wrapper)
    signal.signal(signal.SIGTERM, stop_wrapper)

    try:
        proxy.wait()
    except KeyboardInterrupt:
        proxy.stop()
