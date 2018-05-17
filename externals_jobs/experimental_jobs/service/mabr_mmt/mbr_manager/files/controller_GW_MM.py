#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
# Author:  / <@toulouse.viveris.com>

import re
import os
import sys
import time
import signal
import syslog
import argparse
import multiprocessing
from queue import Queue
from threading import Thread, Lock
from tempfile import NamedTemporaryFile

import norm
import caching
import collect_agent
from scapy.all import *
from scapy.layers import http
from httpget_GW import HttpGetGw

class ControllerProxyMM(object):

    def __init__(
            self, resolution, content_dir, multicast_contents,
            content_name, content_name_short, mpd_date,
            segment_duration, multicast_a_addr, multicast_a_port,
            multicast_b_addr, multicast_b_port, norm_maxrate,
            norm_tx_iface, proxy, server_ip, squid_cache_dir,
            formatted_files_dir):
        # Conf variables
        self._resolution = resolution
        self._content_dir = content_dir
        self._squid_cache_dir = squid_cache_dir
        self._formatted_files_dir = formatted_files_dir
        self._multicast_contents = multicast_contents
        self._content_name = content_name
        self._content_name_short = content_name_short
        self._tx_dir = os.path.join(content_dir,
                                    "{}_{}bps/".format(content_name_short,
                                                       resolution))
        self._mpd_filename = '{}_{}s_simple_{}.mpd'.format(content_name, segment_duration, mpd_date)
        self._segment_duration = segment_duration
        self._multicast_a_addr = multicast_a_addr
        self._multicast_a_port = multicast_a_port
        self._multicast_b_addr = multicast_b_addr
        self._multicast_b_port = multicast_b_port
        self._norm_maxrate = norm_maxrate
        self._norm_tx_iface = norm_tx_iface
        self._proxy = proxy
        self._server_ip = server_ip
        # Status variables
        self._current_groups = {}
        self._last_segment = 1
        # Threads variables
        self._queue = Queue()
        self._lock = Lock()
        self._norm_tx_t = {}
        self._current_segment_t = None
        self._cache_counter_t = None
        self._cache_format_t = None
        self._http = None
        self._starter_t = None
        self._sniffer_t = None
        self._init_threads()
        self._shutdown = False

    def _init_threads(self):
        """ Initialize threads """
        self._cache_counter_t = Thread(target=self._last_segment_counter)
        self._cache_format_t = Thread(target=self._caching)
        self._starter_t = Thread(target=self._start)
        self._sniffer_t = Thread(target=self._sniff)

    def start(self):
        """ Start threads """
        self._cache_counter_t.start()
        self._cache_format_t.start()

        time.sleep(0.2)

        mpd_file = self._mpd_filename
        mp4_file = '{}_{}s_init.mp4'.format(
            self._content_name, self._segment_duration)
        self._http = HttpGetGw(
                self._proxy, self._server_ip, self._content_name,
                self._content_name_short,
                self._segment_duration, mpd_file, mp4_file, self._resolution)
        self._http.start()
        self._starter_t.start()
        # Start sniffing
        self._sniffer_t.start()

    def wait(self, timeout=None):
        """ Wait on all threads """
        time.sleep(1)
        for thread in set(self._norm_tx_t.values()) | { self._cache_counter_t,
                self._cache_format_t, self._starter_t, self._sniffer_t }:
            if thread.is_alive():
                try:
                    thread.terminate()
                except AttributeError:
                    pass
                thread.join(timeout)

    def stop(self):
        """ Stop all threads """
        self._shutdown = True
        subprocess.call(
                "sed -n -r -i '/{}(.+)/!p' {}".format(
                        self._content_name,self._multicast_contents),
                shell=True)
        if self._http:
            self._http.stop()
        self.wait(1)

    def _start(self):
        """ Main for starter thread """
        # Wait until mpd file is present
        while self._mpd_filename not in os.listdir(self._content_dir):
            if self._shutdown:
                return
        
        original_mpd_filepath = os.path.join(self._content_dir, self._mpd_filename)
        resolution_pattern = re.compile(r'<Representation(.+)bandwidth="([0-9]+)"')

        # Open old file and remove wrong resolutions
        with open(original_mpd_filepath) as openfile:
            mpd_content = []
            for line in openfile:
                resolution_found = resolution_pattern.search(line)
                if resolution_found and int(resolution_found.group(2)) != self._resolution:
                    continue
                mpd_content.append(line)

        # Write new file
        with open(os.path.join(self._tx_dir, self._mpd_filename), 'w') as openfile:
            openfile.writelines(mpd_content)

        collect_agent.send_log(syslog.LOG_DEBUG, "CONTROLLER: Starting NORM Tx")

        # TODO: find a way to not use sed        
        subprocess.call(
                'sudo sed -i -e "\$a{0} (P3) --- {1}:{2}:{3}/{4}" {5}'.format(
                    self._content_name, self._multicast_a_addr,
                    self._multicast_a_port, -1, "last",
                    self._multicast_contents), shell= True)

        with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as temp_file:
            filename = temp_file.name
            
        self._current_groups[self._multicast_a_addr] = self._multicast_a_port
        self._norm_tx_t[self._multicast_a_addr]= Thread(
                target=norm.send_mode,
                args=(self._multicast_a_addr, self._multicast_a_port,
                    self._norm_tx_iface, self._tx_dir, "off", "off",
                    self._norm_maxrate, -1, None, filename, self._queue))
        self._norm_tx_t[self._multicast_a_addr].start()

    def _sniff(self):
        """ Main for sniffer thread """
        sniff(
                iface=self._norm_tx_iface, prn=self._process_packet,
                filter="tcp port 80",
                stop_filter=lambda x: self._shutdown)

    def _last_segment_counter(self):
        """ Main for cache counter thread """
        while not self._shutdown:
            segs_map = map(int,
                re.findall(
                    '{}s([0-9]+)'.format(self._segment_duration),
                    ''.join(os.listdir(self._tx_dir))))
            with self._lock:
                self._last_segment = max(0,*segs_map, self._last_segment)

    def _caching(self):
        """ Cache format thread function """
        while not self._shutdown:
            caching.cache(
                    self._squid_cache_dir, self._formatted_files_dir,
                    self._server_ip, self._segment_duration,
                    self._content_name, self._content_name_short)
            time.sleep(1)
    
    def _process_packet(self, packet):
        """ Process a sniffed IP packet """

        if ( not packet.haslayer(http.HTTPRequest) or
            packet.getlayer(http.HTTPRequest).fields['Method'] != 'GET' ):
            return

        http_layer = packet.getlayer(http.HTTPRequest)
        uri = packet.getlayer(http.HTTPRequest).fields['Path']
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        
        with open(self._multicast_contents) as openfile:
            for line in openfile:
                content_name = line.split(' ')[0]
                if content_name not in uri:
                    continue
                match= re.search(
                        "{0}_{1}s([0-9]+)_{1}s([0-9]+)[.]m4s".format(
                                content_name, self._segment_duration),
                        uri)
                if not match:
                    continue
                first_seg, last_seg = int(match.group(1)), int(match.group(2))
                first_seg = -1 if first_seg in {0, 1} else first_seg
                # TODO: find way to avoid using sed
                subprocess.call('sudo sed -i -e "s/{0} (P3)/& --- {1}:{2}:{3}\/{4}/" {5}'.format(
                        content_name, self._multicast_b_addr,
                        self._multicast_b_port, first_seg, last_seg,
                        self._multicast_contents), shell=True)

                # Create thread
                with NamedTemporaryFile(prefix='normSocket',dir='/tmp/') as temp_file:
                    filename = temp_file.name

                time.sleep(4)
                self._current_groups[self._multicast_b_addr] = self._multicast_b_port
                self._norm_tx_t[self._multicast_b_addr] = Thread(
                        target=norm.send_mode,
                        args=(self._multicast_b_addr, self._multicast_b_port,
                            self._norm_tx_iface, self._tx_dir, "off", "off", self._norm_maxrate,
                            first_seg, last_seg, filename, None))
                self._norm_tx_t[self._multicast_b_addr].start()
        
if __name__ == '__main__':
    
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
            '--resolution', type=int, default=4219897,
            help='The resolution of the content')
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
            default=1000000, help='Norm maxrate')

    args = parser.parse_args()

    conffile = '/opt/openbach/agent/jobs/twinkle_voip/mbr_manager_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    controller = ControllerProxyMM(
            args.resolution, args.content_dir, args.multicast_contents,
            args.content_name, args.content_name_short, args.mpd_date,
            args.segment_duration, args.multicast_a_address, args.multicast_a_port,
            args.multicast_b_address, args.multicast_b_port, args.norm_maxrate,
            args.norm_tx_iface, args.proxy_url, args.server_ip, args.squid_cache_dir,
            args.formatted_files_dir)
    controller.start()

    def stop_wrapper(sig_number, stack_frame):
        controller.stop()

    signal.signal(signal.SIGINT, stop_wrapper)
    signal.signal(signal.SIGTERM, stop_wrapper)

    try:
        controller.wait()
    except KeyboardInterrupt:
        controller.stop()
