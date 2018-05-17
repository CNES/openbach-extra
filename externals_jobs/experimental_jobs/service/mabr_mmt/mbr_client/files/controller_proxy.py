#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
# Author:  / <@toulouse.viveris.com>

import os
import re
import sys
import stat
import time
import signal
import syslog
import argparse
import subprocess
import multiprocessing
from threading import Thread, Lock
from tempfile import NamedTemporaryFile

import iptc
import norm
import collect_agent
from scapy.all import *
from scapy.layers import http
from httpget_PROXY import HttpGetProxy

class ControllerProxy(object):

    def __init__(
            self, rx_norm_iface, rx_norm_dir, descriptor_address,
            descriptor_port, contents_descriptor_file,
            segment_duration, mpd_dir, proxy_url, resolutions, content_name,
            content_name_short, server_ip, priorities, squid_cache_dir,
            max_cache_size, firsts_chunks):
        # Conf variables
        self._rx_norm_iface = rx_norm_iface
        self._rx_norm_dir = rx_norm_dir
        self._mpd_dir = mpd_dir
        self._proxy_url = proxy_url
        self._resolutions = resolutions
        self._content_name = content_name
        self._content_name_short = content_name_short
        self._contents_descriptor_file = contents_descriptor_file
        self._segment_duration = segment_duration
        self._server_ip = server_ip
        self._priorities = priorities
        self._squid_cache_dir = squid_cache_dir
        self._max_cache_size = max_cache_size
        self._firsts_chunks = firsts_chunks
        self._descriptor_address = descriptor_address
        self._descriptor_port = descriptor_port
        # Status variables
        self._last_segment = 0
        self._switched = False
        self._current_rx_contents = defaultdict(list)
        self._iptc_rule = None
        self._iptc_chain = None
        self._first_time = True
        # Thread variables
        self._lock = Lock()
        self._shutdown = False
        self._worker_t = None
        self._sniffer_t = None
        self._norm_rx_t = {}
        self._proxy = None
        self._process_contents_list_t = None
        self._get_firsts_chunks_t = None
        self._rx_contents_descriptor_t = None
        self._init_threads()

    def _init_threads(self):
        """ Initialices threads """
        self._worker_t = Thread(target=self._worker)
        self._sniffer_t = Thread(target=self._sniff)
        self._process_contents_list_t = Thread(target=self._process_contents_list)
        self._get_firsts_chunks_t = Thread(target=self._get_firsts_chunks)
        self._rx_contents_descriptor_t = Thread(target=self._rx_contents_descriptor)

    def _check_continuity(self, first, last):
        """ Check if all segments between first and last are present """
        segments = set(map(int, 
            re.findall('2s([0-9]+)', ''.join(os.listdir(self._rx_norm_dir)))))
        return all(( segment in segments for segment in range(first, last+1) ))

    def start(self):
        """ Starts the threads """
        # Start threads
        self._worker_t.start()
        self._sniffer_t.start()
        self._process_contents_list_t.start()
        self._rx_contents_descriptor_t.start()
        if self._firsts_chunks == "on":
            self._get_firsts_chunks_t.start()

    def wait(self, timeout=None):
        """ Wait on threads """
        # Don't wait for sniffer thread, it can't be stopped
        for thread in set(self._norm_rx_t.values()) | { self._worker_t }:
            if thread and thread.is_alive():
                try:
                    thread.terminate()
                except AttributeError:
                    pass
                thread.join(timeout)
         
    def stop(self):
        """ Stop all threads """
        self._shutdown = True

        # Delete ip rule
        if self._iptc_rule:
            self._iptc_chain.delete_rule(self._iptc_rule)

        if self._proxy:
            self._proxy.stop()
        self.wait(1)
        os.remove(self._contents_descriptor_file)

    def _sniff(self):
        """ Sniffer thread function """
        sniff(
            iface=self._rx_norm_iface, prn=self._process_packet,
            filter="tcp port 80", stop_filter=lambda x: self._shutdown)

    def _worker(self):
        """ Thread worker function """
        while not self._shutdown:
            seg_list = map(int, 
                re.findall('2s([0-9]+)', ''.join(os.listdir(self._rx_norm_dir))))
            with self._lock:
                self._last_segment = max(0, self._last_segment, *seg_list)

    def _rx_contents_descriptor(self):
        with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as temp_file:
            filename = temp_file.name
        rx_directory = self._contents_descriptor_file[:self._contents_descriptor_file.rfind('/')+1]
        self._norm_rx_t[self._descriptor_address]=multiprocessing.Process(
                target=norm.receive_mode,
                args=(self._descriptor_address, self._descriptor_port,
                      self._rx_norm_iface,
                      rx_directory, "off", filename))
        self._norm_rx_t[self._descriptor_address].start()
        collect_agent.send_log(syslog.LOG_DEBUG,
                "RUNNING NORM for contents descriptor "
                "file on address {}/{}".format(
                        self._descriptor_address,self._descriptor_port))
        while not self._shutdown:
            pass

    def _get_infos(self,group):
        infos = group.split(':')
        address = infos[0]
        port = infos[1]
        first_seg = infos[2].split('/')[0]
        last_seg = infos[2].split('/')[1]
        return(address,port,first_seg,last_seg)

    def _stop_background_rx(self):
        """ Terminate all the processes wich receive on background """
        for content in self._current_rx_contents.keys():
            for address in self._current_rx_contents[content]:
                collect_agent.send_log(syslog.LOG_DEBUG, 'STOPPING : {} {}'.format(content,self._current_rx_contents[content]))
                self._norm_rx_t[address].terminate()
                self._norm_rx_t[address].join()


    def _process_contents_list(self):
        """ Run Norm to receive contents according to their priorities """
        while not self._shutdown:
            while (not os.path.exists(self._contents_descriptor_file) or os.stat(self._contents_descriptor_file).st_mode & (stat.S_IXGRP | stat.S_ISGID) == stat.S_ISGID):
                pass

            cmd = 'du -s {}'.format(self._squid_cache_dir)
            cmd_result = subprocess.check_output(cmd,shell=True)
            cache_size_pattern = re.search('([0-9]+).*{}'.format(self._squid_cache_dir),cmd_result.decode())
            cache_size = int(cache_size_pattern.group(1))

            if cache_size >= self._max_cache_size:
                collect_agent.send_log(syslog.LOG_DEBUG, 'Warning : Cache is full. Stopping Norm for low priority contents')
                self._stop_background_rx()
                break

            with open(self._contents_descriptor_file) as openfile:
                for line in openfile:
                    content, *groups = line.rstrip().split(' --- ')
                    name_and_prio = re.search('(.+) \(P([0-9]+)\)', content)
                    if (name_and_prio is None):
                        continue
                    content_name = name_and_prio.group(1)
                    prio = name_and_prio.group(2)

                    if prio not in self._priorities or content_name == self._content_name:
                        continue
                    with self._lock:
                        for group in groups:
                            address, port, first_seg, last_seg = self._get_infos(group)
                            if address in self._norm_rx_t:
                                continue
                            self._current_rx_contents[content_name].append(address)
                            with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as temp_file:
                                filename = temp_file.name
                            self._norm_rx_t[address]=multiprocessing.Process(
                                    target=norm.receive_mode,
                                    args=(address, int(port),
                                          self._rx_norm_iface,
                                          self._rx_norm_dir, "off", filename))
                            self._norm_rx_t[address].start()
                            collect_agent.send_log(syslog.LOG_DEBUG, "RUNNING NORM : {} {} ({} with Priority {})".format(address, port, content_name, prio))
            time.sleep(0.5)

    def _get_firsts_chunks(self):
        """ Get all the init.mp4 files that are being sent """
        current_contents = defaultdict(list)

        if self._first_time:
            while(not os.path.exists(self._contents_descriptor_file) or os.stat(self._contents_descriptor_file).st_mode & (stat.S_IXGRP | stat.S_ISGID) == stat.S_ISGID):
                pass
            with open(self._contents_descriptor_file) as openfile:
                for line in openfile:
                    content, *groups = line.rstrip().split(' --- ')
                    name_and_prio = re.search('(.+) \(P([0-9]+)\)', content)
                    if (name_and_prio is None):
                        continue
                    content_name = name_and_prio.group(1)

                    if content_name == self._content_name:
                        continue
                    with self._lock:
                        for group in groups:
                            address, port, first_seg, last_seg = self._get_infos(group)
                            current_contents[content_name].append(address)

            self._first_time = False

        while not self._shutdown:
            while(not os.path.exists(self._contents_descriptor_file) or os.stat(self._contents_descriptor_file).st_mode & (stat.S_IXGRP | stat.S_ISGID) == stat.S_ISGID):
                pass
            with open(self._contents_descriptor_file) as openfile:
                for line in openfile:
                    content, *groups = line.rstrip().split(' --- ')
                    name_and_prio = re.search('(.+) \(P([0-9]+)\)', content)
                    if (name_and_prio is None):
                        continue
                    content_name = name_and_prio.group(1)

                    if content_name == self._content_name:
                        continue

                    with self._lock:
                        for group in groups:
                            address, port, first_seg, last_seg = self._get_infos(group)
                            if content_name in current_contents and address in current_contents[content_name]:
                                continue
                            current_contents[content_name].append(address)

                            if address in self._norm_rx_t:
                                continue
                            with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as temp_file:
                                filename = temp_file.name
                            self._norm_rx_t[address]=multiprocessing.Process(
                                    target=norm.receive_mode,
                                    args=(address, int(port),
                                          self._rx_norm_iface,
                                          self._rx_norm_dir,
                                          "on", filename))
                            self._norm_rx_t[address].start()
                            collect_agent.send_log(syslog.LOG_DEBUG, "RUNNING NORM : {} {} (Getting first chunk for {})".format(address, port, content_name))

            time.sleep(0.5)

    def _process_packet(self, packet):
        """ Process a sniffed IP packet """
        # Consider only HTTP packets
        if (not packet.haslayer(http.HTTPRequest) or
                packet.getlayer(http.HTTPRequest).fields['Method'] != 'GET' ):
            return

        http_layer = packet.getlayer(http.HTTPRequest)
        uri = packet.getlayer(http.HTTPRequest).fields['Path']

        try:
            segment_num = int(re.findall(
                '{}s([0-9]+)'.format(self._segment_duration), uri)[0])
        except IndexError:
            return

        while(not os.path.exists(self._contents_descriptor_file) or os.stat(self._contents_descriptor_file).st_mode & (stat.S_IXGRP | stat.S_ISGID) == stat.S_ISGID):
            pass

        with open(self._contents_descriptor_file) as openfile:
            for line in openfile:
                content, *groups = line.rstrip().split(' --- ')
                name_and_prio = re.search('(.+) \(P([0-9]+)\)', content)
                if name_and_prio is None or name_and_prio.group(1) not in uri:
                    continue
                content_name = name_and_prio.group(1)
                for group in groups:
                    # Unpack values
                    address, port, first_seg, last_seg = self._get_infos(group)

                    # Check if addresed at me
                    for_me = True if last_seg == "last" else (int(segment_num) <  int(last_seg))

                    # Check if a thread exists that process this connection
                    if not for_me or address in self._norm_rx_t:
                        continue
                    # If not, create a new thread
                    with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as temp_file:
                        filename = temp_file.name
                    self._norm_rx_t[address] = multiprocessing.Process(
                            target=norm.receive_mode,
                            args=(address, int(port), self._rx_norm_iface,
                                  self._rx_norm_dir, "off", filename))
                    self._norm_rx_t[address].start()
                    collect_agent.send_log(syslog.LOG_DEBUG, "RUNNING NORM : {} {} from s{} to s{} ({} with Priority 0)".format(address, port,first_seg,last_seg, content_name))
                break

        with self._lock:
            last_segment = self._last_segment
        collect_agent.send_log(syslog.LOG_DEBUG, "Unicast request: {}".format(segment_num))
        collect_agent.send_log(syslog.LOG_DEBUG, "In cache: {}".format(last_segment))

        if not self._check_continuity(segment_num, segment_num + 3) or self._switched:
            return

        collect_agent.send_log(syslog.LOG_DEBUG, "Switch to multicast")
        rule = iptc.Rule()
        rule.protocol = 'tcp'
        rule.dst = self._server_ip
        match = rule.create_match('tos')
        match.tos = '0x28'
        target = rule.create_target('REDIRECT')
        target.__to_port = "8080"
        chain = iptc.Chain(iptc.Table(iptc.Table.NAT), 'OUTPUT')
        chain.insert_rule(rule)
        self._iptc_rule = rule
        self._iptc_chain = chain
        # Flush conntrack
        subprocess.call(['conntrack', '-F'])

        self._proxy = HttpGetProxy(
                True, self._rx_norm_dir, self._mpd_dir, self._proxy_url,
                self._server_ip, self._resolutions, self._content_name,
                self._content_name_short, self._segment_duration, first_seg=1)
        self._proxy.start()
        # Indicate that switch has been made
        self._switched = True

if __name__ == '__main__':
    def proxy_type(arg):
        return { arg.split(':')[0] : ':'.join(arg.split(':')[1:]) }

    def comma_separated_list(arg):
        return set(map(str.strip, arg.split(',')))

    parser = argparse.ArgumentParser(
            description='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            'rx_norm_iface', type=str, help='Norm Tx interface')
    parser.add_argument(
            'rx_norm_dir', type=str, help='Norm Tx interface')
    parser.add_argument(
            'descriptor_address', type=str,
            default='224.1.2.10', help='Multicast address to Rx the contents descriptor file')
    parser.add_argument(
            'descriptor_port', type=int,
            default='6010', help='Multicast port to Rx the contents descriptor file')
    parser.add_argument(
            'squid_cache_dir', type=str, help='The squid cache directory')
    parser.add_argument(
            'contents_descriptor_file', type=str,
            help='Path of the file containing the contents')
    parser.add_argument(
            'segment_duration', type=int,
            help='The duration of each video segment')
    parser.add_argument(
            'mpd_dir', type=str,
            help='The directory where the mpd file is located')
    parser.add_argument(
            'proxy_url', type=proxy_type,
            help='The proxy url')
    parser.add_argument(
            '--resolutions', type=comma_separated_list,
            default={1546902, 334349, 4219897, 45652},
            help='The contents resolutions')
    parser.add_argument('content_name', type=str, help='The content name')
    parser.add_argument('content_name_short', type=str, help='The short content name')
    parser.add_argument('server_ip', type=str, help='The IP of the server')
    parser.add_argument(
            '--priorities', type=comma_separated_list,
            default={1},
            help='The priorities of contents to receive')
    parser.add_argument(
            'max_cache_size', type=int,
            default=1000000,
            help='The maximal amount of content allowed in the cache in KB')
    parser.add_argument(
            '--firsts-chunks', type=str, default='on',
            help='If enabled, gets all the firsts chunks available')

    args = parser.parse_args()

    conffile = '/opt/openbach/agent/jobs/twinkle_voip/mbr_client_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    controller = ControllerProxy(
            args.rx_norm_iface, args.rx_norm_dir, args.descriptor_address,
            args.descriptor_port, args.contents_descriptor_file,
            args.segment_duration, args.mpd_dir, args.proxy_url, args.resolutions,
            args.content_name, args.content_name_short, args.server_ip,
            args.priorities, args.squid_cache_dir, args.max_cache_size,
            args.firsts_chunks)
    controller.start()

    def stop_wrapper(sig_number, stack_frame):
        controller.stop()

    signal.signal(signal.SIGINT, stop_wrapper)
    signal.signal(signal.SIGTERM, stop_wrapper)

    try:
        controller.wait()
    except KeyboardInterrupt:
        controller.stop()
