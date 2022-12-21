#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#   
#   
#   Copyright © 2016-2023 CNES
#   
#   
#   This file is part of the OpenBACH testbed.
#   
#   
#   OpenBACH is a free software : you can redistribute it and/or modify it under the
#   terms of the GNU General Public License as published by the Free Software
#   Foundation, either version 3 of the License, or (at your option) any later
#   version.
#   
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
#   details.
#   
#   You should have received a copy of the GNU General Public License along with
#   this program. If not, see http://www.gnu.org/licenses/.

""" Sources of the Job vlc """

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
 * Francklin SIMO <francklin.simo@toulouse.viveris.com>
'''

import sys
import math
import time
import socket
import syslog
import argparse
import subprocess

import telnetlib

import collect_agent


DESCRIPTION = 'This job launches VLC tool (sender or receiver mode) in order to send or receive a video stream. Statistics about medias contained in this video are sent by the receiver. You would start sender first'

DEFAULT_VIDEO='/opt/openbach/agent/jobs/vlc/bigbuckbunny.mp4'
DEFAULT_PORT=6000
MRL = "rtp://{}:{}"
CLI = "cli={{host='telnet://localhost:{}', password='vlc'}}"
STATS_TO_SEND = ['demux bytes read', 'demux bitrate', 'frames displayed', 'frames lost']


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('localhost', 0))
        return sock.getsockname()[1]


def multiplier (unit):
    if unit.startswith('B') or unit.startswith('b'):
        return 1
    if unit.startswith('Ki') or unit.startswith('kb'):
        return 1024
    if unit.startswith('Mi') or unit.startswith('mb'):
        return 1024 * 1024
    if unit.startswith('Gi') or unit.startswith('gb'):
        return 1024 * 1024 * 1024
    collect_agent.send_log(syslog.LOG_ERR, 'Units of vlc metrics are not availables/correct')
    return 1


def receive(dst_ip, port, duration, interval):
    mrl = MRL.format(dst_ip, port)
    # Find an available port
    vlc_port = find_free_port()
    if vlc_port is None:
        collect_agent.send_log(syslog.LOG_ERR, "No ports available to bind VLC control interface")
        sys.exit(1)   
    # Start to play network media
    cmd = ["vlc-wrapper", "-V", "dummy", "-I", "cli", "--lua-config", CLI.format(vlc_port), mrl]
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (IndexError, ValueError) as ex:
        collect_agent.send_log(syslog.LOG_ERR, 'Problem when launching VLC: {}'.format(ex))
        sys.exit(1)
        
    connected = False
    ref = int(time.time())
    # Connect to vlc terminal if the process is still running and Wait for telnet server start before retrieve stats
    while p.poll() is None and (time.time() - ref) < duration:
        if not connected:
            try:
                tn = telnetlib.Telnet(host='localhost', port=vlc_port)
                tn.read_until(b"Password: ")
                tn.write('vlc'.encode('ascii') + b"\n")
                connected = True
            except ConnectionRefusedError as ex:
                continue
        if connected:
            statistics = dict()
            try:
                tn.read_until(b">")
                tn.write(b"stats\n")
                lines = list(map(lambda l: l.decode().replace('\r',''), tn.read_until(b"end of statistical info").split(b"\n")))
            except EOFError as ex:
                break
            for line in lines:
                if line.startswith("|") and ':' in line:
                    tokens = line.replace('|','').split(":")
                    value_units = tokens[1].strip().split(" ")
                    if len(value_units) > 1:
                        stat, value = tokens[0].strip(), int(value_units[0]) * multiplier(value_units[1])
                    else:
                        stat, value = tokens[0].strip(), int(value_units[0])
                    if stat in STATS_TO_SEND:
                        statistics.update({stat:value})
            collect_agent.send_stat(collect_agent.now(), **statistics)
            time.sleep(interval)
            
    if p.poll() is None:
        p.kill()
    if p.returncode == 1:
        collect_agent.send_log(syslog.LOG_ERR, "VLC has unexpectedly exited because: {}".format(p.stderr.read().decode()))


def send(dst_ip, port, filename, vb, ab, duration):
    # Connect to collect agent
    conffile = '/opt/openbach/agent/jobs/vlc/vlc.conf'
    collect_agent.register_collect(conffile)
    collect_agent.send_log(syslog.LOG_DEBUG, "About to launch VLC job")

    # Launch VLC
    if vb or ab:
        sout = "#transcode{{vcodec=mp4v,acodec=mpga,{0}{1}deinterlace}}".format(
                "vb={},".format(vb) if vb else '',
                "ab={},".format(ab) if ab else '')
        sout += ":rtp{{dst={0},port={1},sdp=sap,mux=ts}}".format(dst_ip, port)
    else:
        sout = "#rtp{{dst={0},port={1},sdp=sap,mux=ts}}".format(dst_ip, port)
    
    cmd = ["vlc-wrapper", "-q", filename, "-Idummy", "--sout", sout, "--sout-keep", "--loop"]
    try:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except (IndexError, ValueError) as ex:
        collect_agent.send_log(syslog.LOG_ERR, "Problem when launching VLC: {}".format(ex))

    if duration == math.inf:
        p.wait()
    else:
        time.sleep(duration)
        p.kill()
    if p.returncode == 1:
        collect_agent.send_log(syslog.LOG_ERR, "VLC has unexpectedly exited because: {}".format(p.stderr.read().decode()))


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/vlc/vlc_rstats_filter.conf'):
        # Define usage
        parser = argparse.ArgumentParser(description=DESCRIPTION,
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        # Sender or receiver arguments
        parser.add_argument("dst_ip", type=str,
                            help='The destination IP address'
        )
        parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
                            help="The destination port"
        )
        parser.add_argument('-d', '--duration', type=int, default=math.inf,
                            help='The duration of the transmission/reception, in seconds (Default: infinite)'
        )
        
        # Sub-commands functionnality to split 'sender' mode and 'receiver' mode
        subparsers = parser.add_subparsers(
                title='Subcommand mode',
                help='Choose the vlc mode (sender mode or receiver mode)'
        )
        subparsers.required=True
        # Sender specific arguments
        parser_sender = subparsers.add_parser('sender', help='Run in sender mode')
                                         
        parser_sender.add_argument('-f', '--filename', type=str, 
                                  default=DEFAULT_VIDEO, 
                                  help='The filename to stream'
        )
        parser_sender.add_argument('-v', '--vb', type=int, 
                                  default=0,
                                  help='The video bitrate when transcoding'
        )
        parser_sender.add_argument('-a', '--ab', type=int, 
                                  default=0,
                                  help='The audio bitrate when transcoding'
        )
        # Receiver specific arguments
        parser_receiver = subparsers.add_parser('receiver', help='Run in receiver mode')
        parser_receiver.add_argument('-i', '--interval', type=float, 
                          default=1,
                          help='The period in seconds to retrieve and send statistics (Default: 1s)'
        )
        
        # Set subparsers options to automatically call the right
        # function depending on the chosen subcommand
        parser_sender.set_defaults(function=send)
        parser_receiver.set_defaults(function=receive)
        
        # Get args and call the appropriate function
        args = vars(parser.parse_args())
        main = args.pop('function')
        main(**args)
