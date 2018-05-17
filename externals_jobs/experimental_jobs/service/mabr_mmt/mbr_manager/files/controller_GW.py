#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
# Author:  / <@toulouse.viveris.com>

import os
import re
import sys
import time
import signal
import syslog
import argparse
import multiprocessing
from threading import Thread, Lock
from tempfile import NamedTemporaryFile

import norm
import caching
import collect_agent
from scapy.all import *
from scapy.layers import http
from httpget_GW import HttpGetGw

class ControllerProxy(object):

    def __init__(
            self, norm_tx_iface, server_ip, content_dir,
            squid_cache_dir, formatted_files_dir,
            multicast_contents, quality, resolutions,
            content_name, content_name_short, segment_duration,
            multicast_a_addr, multicast_a_port,
            multicast_b_addr, multicast_b_port,
            norm_maxrate, proxy_url, mpd_date):
        # Conf variables
        self._norm_tx_iface = norm_tx_iface
        self._tx_dir = None
        self._content_dir = content_dir
        self._squid_cache_dir = squid_cache_dir
        self._formatted_files_dir = formatted_files_dir
        self._multicast_contents = multicast_contents
        self._resolutions = resolutions
        self._quality_policy = quality
        self._content_name = content_name
        self._content_name_short = content_name_short
        self._segment_duration = segment_duration
        self._multicast_a_addr = multicast_a_addr
        self._multicast_a_port = multicast_a_port
        self._multicast_b_addr = multicast_b_addr
        self._multicast_b_port = multicast_b_port
        self._norm_maxrate = norm_maxrate
        self._server_ip = server_ip
        self._proxy_url = proxy_url
        self._mpd_date = mpd_date
        # Status variables
        self._um = False # Unicast mode
        self._mm = False # Multicast mode
        self._transition = False
        self._st1_ready = False
        self._st2_ready = False
        self._um_source = "None"
        self._um_source_2 = "None"
        self._um_resolution = None
        self._current_um_segment = 0
        self._current_groups = {}
        self._last_segment = -2
        # Thread variables
        self._shutdown = False
        self._lock = Lock()
        self._norm_tx_t = {}
        self._cache_counter_t = None
        self._cache_format_t = None
        self._sniffer_t = None
        self._proxy = None
        self._init_threads()

    def _init_threads(self):
        """ Initialize threads """
        self._cache_counter_t = Thread(
                target=self._last_segment_counter)
        self._cache_format_t = Thread(
                target=self._caching)
        self._sniffer_t = Thread(
                target=self._sniff)

    def start(self):
        """" Start threads """
        self._cache_format_t.start()
        self._sniffer_t.start()

    def wait(self, timeout=None):
        """ Wait on threads """
        # Don't wait for sniffer thread, it can't be stopped
        time.sleep(1)
        for thread in set(self._norm_tx_t.values()) | { self._cache_counter_t, self._cache_format_t }:
            if thread:
                thread.join(timeout)

    def stop(self):
        """ Stop all threads """
        self._shutdown = True
        subprocess.call(
                "sed -n -r -i '/{}(.+)/!p' {}".format(
                        self._content_name,
                        self._multicast_contents),
                shell=True)
        if self._proxy:
            self._proxy.stop()
        self.wait(1)

    def _sniff(self):
        """ Sniffer thread function """
        sniff(
                iface=self._norm_tx_iface, prn=self._process_packet,
                filter="tcp port 80", stop_filter=lambda x: self._shutdown)

    def _last_segment_counter(self):
        """ Cache counter thread function """
        if not self._tx_dir:
            return
        #with self._lock:
        #    self._last_segment = 0
        while not self._shutdown:
            max_seg = max(map(int,
                re.findall(
                    '{}s([0-9]+)'.format(self._segment_duration),
                    ''.join(os.listdir(self._tx_dir)))))
            with self._lock:
                self._last_segment = max(max_seg, self._last_segment)

    def _caching(self):
        """ Cache format thread function """
        while not self._shutdown:
            caching.cache(
                    self._squid_cache_dir, self._formatted_files_dir,
                    self._server_ip, self._segment_duration,
                    self._content_name, self._content_name_short)
            time.sleep(1)

    def _get_average(self, val1, val2):
        """ Get the average between two resolutions """
        if val1 not in self._resolutions or val2 not in self._resolutions:
            return None
        average = 0.5 * abs(val1 + val2)
        chosen_res = self._resolutions[0]
        offset = abs(average - chosen_quality)
        for resolution in self._resolutions:
            if abs(average - resolution) < offset:
                offset = abs(average - resolution)
                chosen_res = resolution
        return chosen_res

    def _process_packet(self, packet):
        """ Process a sniffed IP packet """ 
        if ( not packet.haslayer(http.HTTPRequest) or 
                packet.getlayer(http.HTTPRequest).fields['Method'] != 'GET' ):
            return

        http_layer = packet.getlayer(http.HTTPRequest)
        uri = packet.getlayer(http.HTTPRequest).fields['Path']
    
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
       
        s = re.search(
                '([0-9]+)bps.*{}_{}s([0-9]+)\.m4s'.format(
                    self._content_name, self._segment_duration),
                uri)
        try:
            get_request, resolution, segment = s.group(0), int(s.group(1)), int(s.group(2))
        except (IndexError, ValueError,AttributeError):
            return

        collect_agent.send_log(syslog.LOG_DEBUG, "CONTROLLER: Request from {0}: {1}".format(ip_src, get_request))

        if not self._um and not self._mm:
            self._um = True
            self._um_source = ip_src
            self._um_resolution = resolution
            self._current_um_segment = segment

        elif self._um and not self._mm:
            if self._um_source != ip_src and not self._transition:
                self._um_source_2 = ip_src
                self._transition = True

                # TODO: find way of not using sed
                cmd = 'sudo sed -i -e "\$a{0} (P3) --- {1}:{2}:{3}/{4} --- {5}:{6}:{7}/{8}" {9}'
                subprocess.call(cmd.format(
                        self._content_name, self._multicast_b_addr,
                        self._multicast_b_port, 1, self._current_um_segment,
                        self._multicast_a_addr, self._multicast_a_port, 
                        self._current_um_segment, "last", self._multicast_contents),
                    shell=True)
                time.sleep(2)
                return
            
            if self._um_source == ip_src and self._transition:
                self._st1_ready = True
                
            if self._um_source_2 == ip_src and self._transition:
                self._st2_ready = True
                
            if self._um_source_2 == ip_src and  self._st1_ready and self._st2_ready and self._transition:
                self._transition = False
                # Get the quality to send
                if self._quality_policy == 'max':
                    res_to_send = max(self._um_resolution, resolution)
                elif self._quality_policy == 'min':
                    res_to_send = min(self._um_resolution, resolution)
                elif self._quality_policy == 'average':
                    res_to_send = self._get_average(self._um_resolution, resolution)

                self._tx_dir = os.path.join(self._content_dir,
                        '{}_{}bps/'.format(self._content_name_short, res_to_send))

                # Start cache_counter thread
                self._cache_counter_t.start()
                time.sleep(0.1)
                
                # Start http proxy if it's not started
                if not self._proxy:
                    collect_agent.send_log(syslog.LOG_DEBUG, "CONTROLLER: Starting HTTP Requests to the server")
                    mpd_file = '{}_{}s_simple_{}.mpd'.format(
                            self._content_name, self._segment_duration, self._mpd_date)
                    mp4_file = '{}_{}s_init.mp4'.format(
                            self._content_name, self._segment_duration)
                    # All the segments are requested. Improve only to request
                    # the missing. Get since last_segment could not be enough.
                    self._proxy = HttpGetGw(
                            self._proxy_url, self._server_ip, self._content_name,
                            self._content_name_short, self._segment_duration, mpd_file, mp4_file, res_to_send,
                        -1)

                    self._proxy.start()

                with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as temp_file:
                    filename1 = temp_file.name
                self._current_groups[self._multicast_a_addr] = self._multicast_a_port
                self._norm_tx_t[self._multicast_a_addr] = multiprocessing.Process(
                        target=norm.send_mode,
                        args=(self._multicast_a_addr, self._multicast_a_port,
                            self._norm_tx_iface, self._tx_dir, "off", "off",
                            self._norm_maxrate, int(self._current_um_segment),
                            None, filename1, None))
 
                with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as temp_file:
                    filename2 = temp_file.name
                self._current_groups[self._multicast_b_addr] = self._multicast_b_port
                self._norm_tx_t[self._multicast_b_addr] = multiprocessing.Process(
                        target=norm.send_mode,
                        args=(self._multicast_b_addr, self._multicast_b_port,
                            self._norm_tx_iface, self._tx_dir, "off", "off",
                            self._norm_maxrate, 1, int(self._current_um_segment),
                            filename2, None))
                self._norm_tx_t[self._multicast_a_addr].start()
                collect_agent.send_log(syslog.LOG_DEBUG, "RUNNING NORM {} from {} to last segment".format(
                    self._multicast_a_addr, self._current_um_segment))
                self._norm_tx_t[self._multicast_b_addr].start()
                collect_agent.send_log(syslog.LOG_DEBUG, "RUNNING NORM {} from segment 1 to {}".format(
                    self._multicast_b_addr, self._current_um_segment))
                self._mm = True
            elif not self._transition:
                self._current_um_segment = segment
                self._um_resolution = resolution
 
        elif self._um and self._mm and self._um_source == ip_src:
            self._current_um_segment = segment

if __name__ == '__main__':
    def comma_separated_list(arg):
        return list(map(str.strip, arg.split(',')))
    def proxy_type(arg):
        return { arg.split(':')[0] : ':'.join(arg.split(':')[1:]) }

    parser = argparse.ArgumentParser(
            description='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            'norm_tx_iface', type=str, help='Norm Tx interface')
    parser.add_argument(
            'server_ip', type=str, help='The IP address of the server')
    parser.add_argument(
            'content_dir', type=str, help='The directory of the content')
    parser.add_argument(
            'squid_cache_dir', type=str, help='The Squid cache directory')
    parser.add_argument(
            'formatted_files_dir', type=str, help='The dir to store formatted files')
    parser.add_argument(
            'multicast_contents', type=str, help='Path of the file containing the contents')
    parser.add_argument(
            'quality', type=str, choices=['max', 'min', 'average'],
            help='The quality of the content to use')
    parser.add_argument(
            'resolutions', type=comma_separated_list,
            help='The available of the content')
    parser.add_argument(
            'content_name', type=str,
            help='The name of the content')
    parser.add_argument(
            'content_name_short', type=str,
            help='The short name of the content')
    parser.add_argument(
            'segment_duration', type=int,
            help='The duration of each video segment')
    parser.add_argument(
            'proxy_url', type=proxy_type,
            help='The proxy url')
    parser.add_argument(
            'mpd_date', type=str,
            help='The date on the name of the mpd file')
    parser.add_argument(
            '--multicast-a-address', type=str,
            default='224.1.2.3', help='Multicast A address')
    parser.add_argument(
            '--multicast-a-port', type=int,
            default=6143, help='Multicast A port')
    parser.add_argument(
            '--multicast-b-address', type=str,
            default='224.1.2.4', help='Multicast B address')
    parser.add_argument(
            '--multicast-b-port', type=int,
            default=6142, help='Multicast B port')
    parser.add_argument(
            '--norm-maxrate', type=int,
            default=7000000, help='Norm maximal rate')


    args = parser.parse_args()

    conffile = '/opt/openbach/agent/jobs/twinkle_voip/mbr_manager_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    controller = ControllerProxy(
            args.norm_tx_iface, args.server_ip, args.content_dir,
            args.squid_cache_dir, args.formatted_files_dir,
            args.multicast_contents, args.quality, args.resolutions,
            args.content_name, args.content_name_short, args.segment_duration,
            args.multicast_a_address, args.multicast_a_port,
            args.multicast_b_address, args.multicast_b_port,
            args.norm_maxrate, args.proxy_url, args.mpd_date)
    controller.start()

    def stop_wrapper(sig_number, stack_frame):
        controller.stop()

    signal.signal(signal.SIGINT, stop_wrapper)
    signal.signal(signal.SIGTERM, stop_wrapper)

    try:
        controller.wait()
    except KeyboardInterrupt:
        controller.stop()
