#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#   
#   
#   Copyright © 2017 CNES
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
'''

DEFAULT_VIDEO='/opt/openbach/agent/jobs/vlc/bigbuckbunny.mp4'
DEFAULT_PORT=6000

import subprocess
import argparse
import select
import os
import syslog
import collect_agent
import time
import sys

def main(dst_ip, port, filename, vb, ab, duration):
    # Connect to collect agent
    conffile = '/opt/openbach/agent/jobs/vlc/vlc.conf'
    collect_agent.register_collect(conffile)

    # Launch VLC
    if vb or ab:
        sout = "#transcode{{vcodec=mp4v,acodec=mpga,{0}{1}deinterlace}}".format(
                "vb={},".format(vb) if vb else '',
                "ab={},".format(ab) if ab else '')
        sout += ":rtp{{dst={0},port={1},sdp=sap}}".format(dst_ip, port)
    else:
        sout = "#rtp{{dst={0},port={1},sdp=sap}}".format(dst_ip, port)
    
    cmd = ["vlc", "-q", filename, "-Idummy", "--sout", sout, "--sout-keep", "--loop"]
    p = subprocess.Popen(cmd)
    if duration == 0:
        p.wait()
    else:
        time.sleep(duration)
        p.kill()
 

if __name__ == "__main__":
    # Define usage
    parser = argparse.ArgumentParser(description='',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("dst_ip", type=str,
                        help='The destination IP address')
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
                        help="The dst port")
    parser.add_argument('-f', '--filename', type=str, default=DEFAULT_VIDEO,
                        help='The filename to stream')
    parser.add_argument('-v', '--vb', type=int, default=0,
                        help='The video bitrate when transcoding')
    parser.add_argument('-a', '--ab', type=int, default=0,
                        help='The audio bitrade when transcoding')
    parser.add_argument('-d', '--duration', type=int, default=0,
                        help='The duration (Default: 0 infinite')
    
    # Get arguments
    args = parser.parse_args()
    dst_ip = args.dst_ip
    filename = args.filename
    vb = args.vb
    ab = args.ab
    port = args.port
    duration = args.duration
    
    main(dst_ip, port, filename, vb, ab, duration)
