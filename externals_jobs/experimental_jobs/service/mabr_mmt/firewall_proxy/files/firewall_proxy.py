#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""A basic transparent HTTP proxy"""

__author__ = "Erik Johansson"
__email__  = "erik@ejohansson.se"
__license__= """
Copyright (c) 2012 Erik Johansson <erik@ejohansson.se>
 
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
USA

"""

import re
import sys
import time
import socket
import syslog
import argparse
import requests
import subprocess
from threading import Lock

import collect_agent
from twisted.web import http
from twisted.internet import reactor, protocol
from twisted.python import log

class ProxyClient(http.HTTPClient):
    """ The proxy client connects to the real server, fetches the resource and
    sends it back to the original client, possibly in a slightly different
    form.
    """

    def __init__(self, method, uri, postData, headers, originalRequest):
        self.method = method
        self.uri = uri
        self.postData = postData
        self.headers = headers
        self.originalRequest = originalRequest
        self.contentLength = None

    def sendRequest(self):
        log.msg("Sending request: %s %s" % (self.method, self.uri))
        self.sendCommand(self.method, self.uri)

    def sendHeaders(self):
        for key, values in self.headers:
            if key.lower() == 'connection':
                values = ['close']
            elif key.lower() == 'keep-alive':
                next

            for value in values:
                self.sendHeader(key, value)
        self.endHeaders()

    def sendPostData(self):
        log.msg("Sending POST data")
        self.transport.write(self.postData)

    def connectionMade(self):
        log.msg("HTTP connection made")
        self.sendRequest()
        self.sendHeaders()
        if self.method == 'POST':
            self.sendPostData()

    def handleStatus(self, version, code, message):
        log.msg("Got server response: %s %s %s" % (version, code, message))
        self.originalRequest.setResponseCode(int(code), message)

    def handleHeader(self, key, value):
        if key.lower() == 'content-length':
            self.contentLength = value
        else:
            self.originalRequest.responseHeaders.addRawHeader(key, value)

    def handleResponse(self, data):
        data = self.originalRequest.processResponse(data)

        if self.contentLength != None:
            self.originalRequest.setHeader('Content-Length', len(data))

        self.originalRequest.write(data)

        self.originalRequest.finish()
        self.transport.loseConnection()


class ProxyClientFactory(protocol.ClientFactory):
    def __init__(self, method, uri, postData, headers, originalRequest):
        self.protocol = ProxyClient
        self.method = method
        self.uri = uri
        self.postData = postData
        self.headers = headers
        self.originalRequest = originalRequest

    def buildProtocol(self, addr):
        return self.protocol(self.method, self.uri, self.postData,
                             self.headers, self.originalRequest)

    def clientConnectionFailed(self, connector, reason):
        log.err("Server connection failed: %s" % reason)
        self.originalRequest.setResponseCode(504)
        self.originalRequest.finish()


class ProxyRequest(http.Request):

    # Class attributes
    first_request = True
    first_seg_proxy = -2
    lock = Lock()
    multicast_contents = None
    addr_proxy_bb = None # 102.2
    addr_proxy = None # .102.1
    port_a_proxy_bb = None # 7008
    port_b_proxy_bb = None # 7007
    server_ip = None
    content_name = None
    segment_duration = None

    def __init__(self, channel, queued, reactor=reactor):
        http.Request.__init__(self, channel, queued)
        self.reactor = reactor

    @classmethod
    def configure(cls, conf):
        cls.multicast_contents = conf['multicast_contents']
        cls.addr_proxy_bb = conf['addr_proxy_bb']
        cls.addr_proxy = conf['addr_proxy']
        cls.port_a_proxy_bb = conf['port_a_proxy_bb']
        cls.port_b_proxy_bb = conf['port_b_proxy_bb']
        cls.server_ip = conf['server_ip']
        cls.content_name = conf['content_name']
        cls.segment_duration = conf['segment_duration']

    def process(self):
        host = self.getHeader('host')
        if not host:
            log.err("No host header given")
            self.setResponseCode(400)
            self.finish()
            return

        with open(ProxyRequest.multicast_contents) as openfile:
            for line in openfile:
                if (line.split(' ')[0] not in self.uri.decode()):
                    continue
                # - Send custom request which requests the beginning of the
                # content
                # - At response reception, send rsponse to the ST Proxy end send
                # request of missing content

                with ProxyRequest.lock:
                    if ProxyRequest.first_request == True:
                        sock = socket.socket(socket.AF_INET, # Internet
                                             socket.SOCK_DGRAM) # UDP
                        sock.bind((ProxyRequest.addr_proxy_bb, ProxyRequest.port_b_proxy_bb))

                        while ProxyRequest.first_seg_proxy == -2:
                            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
                            collect_agent.send_log(
                                    syslog.LOG_DEBUG,
                                    "Received message from {0}: {1}".format(addr, data.decode()))
                            ProxyRequest.first_seg_proxy = int(data.decode())

                        collect_agent.send_log(syslog.LOG_DEBUG, "Sending Request to the GW...")
                        url = 'http://{0}/vod-dash/{1}/{2}sec/{1}_{2}s1_{2}s{3}.m4s'.format(
                                ProxyRequest.server_ip,
                                ProxyRequest.content_name,
                                ProxyRequest.segment_duration,
                                ProxyRequest.first_seg_proxy)
                        response = requests.get(url)
                        collect_agent.send_log(syslog.LOG_DEBUG, 'GW Response: {0}'.format(response.status_code))

                        time.sleep(2)

                        collect_agent.send_log(syslog.LOG_DEBUG, "Sending ping to Proxy of ST...")
                        subprocess.run(['ping', ProxyRequest.addr_proxy, '-c', '1'])

                        sock = socket.socket(socket.AF_INET, # Internet
                                             socket.SOCK_DGRAM) # UDP
                        sock.bind((ProxyRequest.addr_proxy_bb, ProxyRequest.port_a_proxy_bb))
                        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
                        collect_agent.send_log(syslog.LOG_DEBUG, "Received message from {0}: {1}".format(addr,data.decode()))

                        ProxyRequest.first_request = False
                        self.setResponseCode(503)
                        self.finish()
                        return
                    self.finish()

        port = 80
        if ':' in host:
            host, port = host.split(':')
            port = int(port)

        self.setHost(host, port)

        self.content.seek(0, 0)
        postData = self.content.read()
        factory = ProxyClientFactory(self.method, self.uri, postData,
                                     self.requestHeaders.getAllRawHeaders(),
                                     self)
        self.reactor.connectTCP(host, port, factory)

    def processResponse(self, data):
        return data


class TransparentProxy(http.HTTPChannel):
    requestFactory = ProxyRequest


class ProxyFactory(http.HTTPFactory):
    protocol = TransparentProxy

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
            description='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('port', type=int, help='The port the proxy is bound to')
    parser.add_argument(
            'multicast_contents', type=str,
            help='The file multicast contents')
    parser.add_argument(
            'addr_proxy_bb', type=str,
            help='The BB proxy IP address')
    parser.add_argument(
            'addr_proxy', type=str,
            help='The proxy IP address')
    parser.add_argument(
            'port_a_proxy_bb', type=int,
            help='The BB proxy A port')
    parser.add_argument(
            'port_b_proxy_bb', type=int,
            help='The BB proxy B port')
    parser.add_argument(
            'server_ip', type=str,
            help='The server IP address')
    parser.add_argument(
            'content_name', type=str,
            help='The name of the content')
    parser.add_argument(
            'segment_duration', type=int,
            help='The duration of a segment')

    args = parser.parse_args()

    conffile = '/opt/openbach/agent/jobs/firewall_proxy/firewall_proxy_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    log.startLogging(sys.stdout)
    ProxyRequest.configure(vars(args))
    reactor.listenTCP(args.port, ProxyFactory())
    reactor.run()
