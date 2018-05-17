#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author:  / <@toulouse.viveris.com>

import re
import os
import sys
import stat
import time
import signal
import syslog
import socket
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

class ControllerProxyMM(object):
    def __init__(
            self, addr_proxy_bb, port_a_proxy_bb, port_b_proxy_bb, rx_norm_dir,
            rx_norm_iface, descriptor_address, descriptor_port,
            contents_descriptor_file, mpd_dir, segment_duration, content_name,
            content_name_short, server_ip, proxy_url, resolutions,
            priorities, squid_cache_dir, max_cache_size, firsts_chunks):
        # Conf variables
        self._addr_proxy_bb = addr_proxy_bb
        self._port_a_proxy_bb = port_a_proxy_bb
        self._port_b_proxy_bb = port_b_proxy_bb
        self._rx_norm_dir = rx_norm_dir
        self._contents_descriptor_file = contents_descriptor_file
        self._mpd_dir = mpd_dir
        self._rx_norm_iface = rx_norm_iface
        self._segment_duration = segment_duration
        self._content_name = content_name
        self._content_name_short = content_name_short
        self._server_ip = server_ip
        self._proxy_url = proxy_url
        self._resolutions = resolutions
        self._priorities = priorities
        self._squid_cache_dir = squid_cache_dir
        self._max_cache_size = max_cache_size
        self._firsts_chunks = firsts_chunks
        self._descriptor_address = descriptor_address
        self._descriptor_port = descriptor_port
        # Status variables
        self._last_segment = -2
        self._first_segment = -2
        self._receiving_multicast = False
        self._current_rx_contents = defaultdict(list)
        self._iptc_rule = None
        self._iptc_chain = None
        self._first_time = True
        # Thread variables
        self._segment_lock = Lock()
        self._proxy = None
        self._switch_to_multicast_t = None
        self._first_seg_sender_t = None
        self._last_seg_getter_t = None
        self._first_seg_getter_t = None
        self._sniffer_t = None
        self._norm_rx_t = {}        # Norm RX threads
        self._shutdown = False      # Shutdown flag
        self._process_contents_list_t = None
        self._get_firsts_chunks_t = None
        self._rx_contents_descriptor_t = None
        self._init_threads()

    def _init_threads(self):
        """ Initialize threads """
        self._switch_to_multicast_t = Thread(target=self._switch_to_multicast)
        self._first_seg_sender_t = Thread(target=self._send_first_seg)
        self._seg_getter_t = Thread(target=self._get_segments)
        self._sniffer_t = Thread(target=self._sniff)
        self._process_contents_list_t = Thread(target=self._process_contents_list)
        self._get_firsts_chunks_t = Thread(target=self._get_firsts_chunks)
        self._rx_contents_descriptor_t = Thread(target=self._rx_contents_descriptor)

    def start(self):
        """ Start the proxy """
        # Start Threads
        self._seg_getter_t.start()
        self._switch_to_multicast_t.start()
        self._sniffer_t.start()
        self._process_contents_list_t.start()
        self._rx_contents_descriptor_t.start()
        if self._firsts_chunks == "on":
            self._get_firsts_chunks_t.start()

    def wait(self, timeout=None):
        """ Wait on threads """
        # Don't wait for sniffer thread, it can't be stopped
        for thread in set(self._norm_rx_t.values()) | { self._seg_getter_t,
                self._first_seg_sender_t, self._switch_to_multicast_t }:
            if thread and thread.is_alive():
                try: 
                    thread.terminate()
                except AttributeError:
                    pass
                thread.join()

    def stop(self):
        """ Signal all threads to stop and wait """
        self._shutdown = True
        if self._iptc_rule:
            self._iptc_chain.delete_rule(self._iptc_rule)
        if self._http:
            self._http.stop()
        os.remove(self._contents_descriptor_file)
        self.wait(1)

    def _sniff(self):
        """ Function for sniffer thread """
        sniff(
            iface=self._rx_norm_iface, prn=self._process_packet,
            filter='(tcp port 80) or (icmp)',
            stop_filter=lambda x: self._shutdown)


    def _get_segments(self):
        """ Update the last_segment and first_segment variables """
        while not self._shutdown:
            segments = set()
            for filename in os.listdir(self._rx_norm_dir):
                segments.update(map(int, re.findall(
                    '{}s([0-9]+)'.format(self._segment_duration),
                    filename)))
            with self._segment_lock:
                self._first_segment, self._last_segment = \
                        (min(segments), max(segments)) if len(segments) else (-2, -2)
            time.sleep(0.1)

    def _check_continuity(self, first, last):
        """ Check if all segments between first and last are present """
        segments = set(map(int, 
            re.findall(
                    '{}s([0-9]+)'.format(self._segment_duration),
                    ''.join(os.listdir(self._rx_norm_dir)))))
        return all(( segment in segments for segment in range(first, last+1) ))

    def _switch_to_multicast(self):
        """ Switch traffic to multicast """
        while not self._shutdown:
            with self._segment_lock:
                last_segment = self._last_segment
            if not self._check_continuity(1,3):
                time.sleep(0.1)
                continue

            collect_agent.send_log(syslog.LOG_DEBUG, "UDP Message sent: OK")
            collect_agent.send_log(syslog.LOG_DEBUG, "-- SWITCH TO MULTICAST --")
            self._send_UDP(self._addr_proxy_bb, self._port_a_proxy_bb, "OK")
            # Redirect traffic to port 8080
            rule = iptc.Rule()
            rule.dst = self._server_ip
            rule.protocol = 'tcp'
            match = rule.create_match('tos')
            match.tos = "0x28"
            target = rule.create_target('REDIRECT')
            target.__to_port = "8080"
            chain = iptc.Chain(iptc.Table(iptc.Table.NAT), 'OUTPUT')
            chain.insert_rule(rule)
            self._iptc_rule = rule
            self._iptc_chain = chain
            # Flush conntrack table
            subprocess.run(['conntrack', '-F'])
            self._http = HttpGetProxy(
                    True, self._rx_norm_dir, self._mpd_dir, self._proxy_url,
                    self._server_ip, self._resolutions, self._content_name,
                    self._content_name_short, self._segment_duration, first_seg=1)
            self._http.start()
            break

    def _send_UDP(self, address, port, message):
        """ Send an UDP message to address:port """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), (address, port))

    def _send_first_seg(self):
        """ Send first segment indefinetely """
        while not self._shutdown:
            self._send_UDP(self._addr_proxy_bb, self._port_b_proxy_bb, str(self._first_segment))
            time.sleep(0.1)

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
        collect_agent.send_log(syslog.LOG_DEBUG, "RUNNING NORM for contents descriptor file on address {}/{}".format(self._descriptor_address,self._descriptor_port))
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
            
            cmd = 'du -s {}'.format(self._squid_cache_dir)
            cmd_result = subprocess.check_output(cmd,shell=True)
            cache_size_pattern = re.search('([0-9]+).*{}'.format(self._squid_cache_dir),cmd_result.decode())
            cache_size = int(cache_size_pattern.group(1))

            if cache_size >= self._max_cache_size:
                collect_agent.send_log(syslog.LOG_DEBUG ,'Warning : Cache is full. Stopping Norm for low priority contents')
                self._stop_background_rx()
                break

            while(not os.path.exists(self._contents_descriptor_file) or os.stat(self._contents_descriptor_file).st_mode & (stat.S_IXGRP | stat.S_ISGID) == stat.S_ISGID):
                pass
            
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
                    with self._segment_lock:
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
                    with self._segment_lock:
                        for group in groups:
                            address, port, first_seg, last_seg = self._get_infos(group)
                            current_contents[content_name].append(address)

            self._first_time = False

        while(not os.path.exists(self._contents_descriptor_file) or os.stat(self._contents_descriptor_file).st_mode & (stat.S_IXGRP | stat.S_ISGID) == stat.S_ISGID):
            pass

        while not self._shutdown:
            with open(self._contents_descriptor_file) as openfile:
                for line in openfile:
                    content, *groups = line.rstrip().split(' --- ')
                    name_and_prio = re.search('(.+) \(P([0-9]+)\)', content)
                    if (name_and_prio is None):
                        continue
                    content_name = name_and_prio.group(1)

                    if content_name == self._content_name:
                        continue

                    with self._segment_lock:
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
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst

        # HTTP packets
        if (packet.haslayer(http.HTTPRequest) and
            packet.getlayer(http.HTTPRequest).fields['Method'] == 'GET' ):

            http_layer = packet.getlayer(http.HTTPRequest)
            uri = packet.getlayer(http.HTTPRequest).fields['Path']

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
                        # Check if a thread exists that process this connection
                        if address in self._norm_rx_t:
                            continue
                        # If not, create a new thread
                        with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as temp_file:
                            filename = temp_file.name
                        self._norm_rx_t[address] = multiprocessing.Process(
                                target=norm.receive_mode,
                                args=(address, int(port), self._rx_norm_iface,
                                    self._rx_norm_dir, "off", filename))
                        self._norm_rx_t[address].start()
                        collect_agent.send_log(syslog.LOG_DEBUG, "RUNNING NORM : {} {} from s{} to s{} ({} with Priority 0)".format(address, port, first_seg, last_seg, content_name))
 
                    if not self._first_seg_sender_t.is_alive():
                        self._first_seg_sender_t.start()
                    self._receiving_multicast = True
                    # Content was found, stop
                    break

        # ICMP packets
        elif ( packet.haslayer(ICMP) and int(packet[ICMP].type) == 8 and
            ip_src == self._addr_proxy_bb and self._receiving_multicast ): 
            collect_agent.send_log(syslog.LOG_DEBUG, 'ICMP RECEIVED')

            while(not os.path.exists(self._contents_descriptor_file) or os.stat(self._contents_descriptor_file).st_mode & (stat.S_IXGRP | stat.S_ISGID) == stat.S_ISGID):
                pass

            with open(self._contents_descriptor_file) as openfile:
                for line in openfile:
                    content, *groups = line.rstrip().split(' --- ')
                    name_and_prio = re.search('(.+) \(P([0-9]+)\)', content)
                    if name_and_prio is None or name_and_prio.group(1) != self._content_name:
                        continue
                    content_name = name_and_prio.group(1)
                    for group in groups:
                        # Unpack values
                        address, port, first_seg, last_seg = self._get_infos(group)
                        # Check if a thread exists that process this connection
                        if address in self._norm_rx_t:
                            continue
                        # If not, create a new thread
                        with NamedTemporaryFile(prefix='normSocket', dir='/tmp/') as temp_file:
                            filename = temp_file.name
                        self._norm_rx_t[address] = multiprocessing.Process(
                                target=norm.receive_mode,
                                args=(address, int(port), self._rx_norm_iface,
                                      self._rx_norm_dir, "off", filename))
                        self._norm_rx_t[address].start()
                        collect_agent.send_log(syslog.LOG_DEBUG, "RUNNING NORM : {} {} from s{} to s{} ({} with Priority 0)".format(address, port, first_seg, last_seg, content_name))
                    # Content was found, stop
                    break


if __name__ == '__main__':
    def proxy_type(arg):
        return { arg.split(':')[0] : ':'.join(arg.split(':')[1:]) }

    def comma_separated_list(arg):
        return set(map(str.strip, arg.split(',')))

    parser = argparse.ArgumentParser(
            description='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            'addr_proxy_bb', type=str, help='Proxy BB address')
    parser.add_argument(
            'port_a_proxy_bb', type=int, help='Proxy BB port A')
    parser.add_argument(
            'port_b_proxy_bb', type=int, help='Proxy BB port B')
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
            help='The maximal amount of caching content in KB')
    parser.add_argument(
            '--firsts-chunks', type=str, default='on',
            help='If enabled, gets all the firsts chunks available')

    args = parser.parse_args()

    conffile = '/opt/openbach/agent/jobs/twinkle_voip/mbr_client_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    controller = ControllerProxyMM(
            args.addr_proxy_bb, args.port_a_proxy_bb, args.port_b_proxy_bb, args.rx_norm_dir,
            args.rx_norm_iface, args.descriptor_address, args.descriptor_port, args.contents_descriptor_file,
            args.mpd_dir, args.segment_duration, args.content_name,
            args.content_name_short, args.server_ip, args.proxy_url,
            args.resolutions, args.priorities, args.squid_cache_dir, args.max_cache_size, args.firsts_chunks)
    controller.start()

    def stop_wrapper(sig_number, stack_frame):
        controller.stop()

    signal.signal(signal.SIGINT, stop_wrapper)
    signal.signal(signal.SIGTERM, stop_wrapper)

    try:
        controller.wait()
    except KeyboardInterrupt:
        controller.stop()
