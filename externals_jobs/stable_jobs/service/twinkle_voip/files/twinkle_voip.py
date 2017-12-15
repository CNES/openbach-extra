#!/usr/bin/python3
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

""" Sources of the job twinkle_voip """

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
'''

import subprocess
import argparse
import select
import time
import fcntl
import re
import os
import random
import syslog
import collect_agent
import sys

TIMEOUT = 5         # timeout for commands
CALL_TIMEOUT = 600  # timeout for calls
DEFAULT_AUDIO = '/opt/openbach/agent/jobs/twinkle_voip/audio.wav'
PORT_MIN = 49152
PORT_MAX = 57500

dev = None     # the sound device to use as mic

def conf(ip, port, nat):
    global dev
    # Load module snd-aloop
    p = subprocess.run(["modprobe", "snd-aloop"],
                         stderr=subprocess.PIPE)
    if p.returncode != 0:
        msg = "Error when loading snd-aloop module (code {}: {})"
        msg = msg.format(p.returncode, p.stderr.decode())
        collect_agent.send_log(syslog.LOG_ERR, msg)
        return False

    # Get the conf files
    
    try:
        home = os.environ["HOME"]
    except KeyError:
        home = '/root'
        os.environ["HOME"] = home
    sys_conf_file = os.path.join(home,'.twinkle/twinkle.sys')
    
    # Get the user name
    username = None
    with open(sys_conf_file, 'r') as f:
        for line in f:
            if line.startswith('start_user_profile'):
                username = line.split('=')[1].strip()
                break
    if not username:
        collect_agent.send_log(syslog.LOG_ERR, "No username found in twinkle.sys")
        return False

    # Check audio conf
    # Search loopback device number
    p1 = subprocess.Popen(["aplay", "-l"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "Loopback"], stdin=p1.stdout, 
                          stdout=subprocess.PIPE)
    p2.wait()
    for line in p2.stdout.read().decode().splitlines():
        if not line.startswith('card'):
           continue
        dev = line.split(':')[0].split(' ')[1]
    if not dev:
        collect_agent.send_log(syslog.LOG_ERR, "No loopback device found")
        return False

    # Update audio conf and the port
    dev_mic = 'dev_mic=alsa:plughw:{},1\n'.format(dev)
    rtp_port = 'rtp_port={}\n'.format(port)
    with open(sys_conf_file) as f:
        conf = [
            'dev_ringtone=alsa:null\n' if line.startswith('dev_ringtone') else
            'dev_speaker=alsa:null\n' if line.startswith('dev_speaker') else
            dev_mic if line.startswith('dev_mic') else 
            rtp_port if line.startswith('rtp_port') else line for line in f
        ]
    with open(sys_conf_file, 'w') as f:
        f.writelines(conf)

    # Update the IP in user conf file
    user_conf_file = os.path.join(home, '.twinkle/{}.cfg'.format(username))
    user_domain = 'user_domain={}\n'.format(ip)
    nat_public_ip = 'nat_public_ip={}\n'.format(ip if nat else '')
    with open(user_conf_file) as f:
        conf = [
            user_domain if line.startswith('user_domain') else 
            nat_public_ip if line.startswith('nat_public_ip') else 
            line for line in f
        ]
    with open(user_conf_file, 'w') as f:
        f.writelines(conf)

    return True

def wait_for(p, string, timeout=TIMEOUT):
    # set stdout to non blocking
    fd = p.stdout.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    # poll stdout
    poll_obj = select.epoll()
    poll_obj.register(p.stdout, select.EPOLLIN)
    rem_time = timeout
    while rem_time > 0:
        poll_result = poll_obj.poll(0)
        if not poll_result:
            time.sleep(0.1) 
            rem_time -= 0.1
            continue
        lines = p.stdout.read().decode().splitlines()
        for line in lines:
            if re.match(".*{}.*".format(string), line):
                return True
    return False

def launch_twinkle():
    # Launch twinkle
    t = subprocess.Popen(["twinkle-console"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not wait_for(t, "Local IP"):
        message = "ERROR when launching twinkle"
        collect_agent.send_log(syslog.LOG_ERR, message)
        t.kill()
        t.wait()
        sys.exit(message)
    return t

def call(p, remote):
    cmd = "call openbach@{}\n".format(remote)
    # Start call
    p.stdin.write(cmd.encode())
    p.stdin.flush()
    
    if not wait_for(p, "200 OK"):
        collect_agent.send_log(syslog.LOG_ERR, "Cannot establish call with server")
        return False
    return True

def finish_call(p):
    # Stop call
    p.stdin.write(b'bye\n')
    p.stdin.flush()

def play_audio(p, audio, length):
    timeout = length
    a = None
    cmd = ["aplay", "-D", "default", audio]
    # Play only once if timeout is 0
    if timeout == 0.0:
        a = subprocess.call(cmd, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
        return
    # Else, play for defined amount of time
    while timeout > 0.0:
        if (a is None) or (a.poll() is not None):
            a = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL) 
        time.sleep(0.1)
        timeout -= 0.1
    a.kill()


def wait_for_call(p):
    # Wait for incoming call
    if not wait_for(p, "incoming call", CALL_TIMEOUT):
        return False

    # accept the call
    p.stdin.write(b'answer\n')
    p.stdin.flush()

    # Wait for call to be established
    return wait_for(p, "established")
    

def close_twinkle(p):
    # Exit twinkle
    p.stdin.write(b'quit\n')
    p.stdin.flush()
    p.wait()

def main(server, remote, audio, length, ip, port, nat):
    # Connect to collect agent
    conffile = '/opt/openbach/agent/jobs/twinkle_voip/twinkle_voip_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    if not server and not remote:
        message = "ERROR must provide a remote address"
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    # Configure
    if not conf(ip, port, nat):
        message = "ERROR when configuring twinkle"
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    # Close twinkle
    t = launch_twinkle()

    # Start or wait for call
    if server:
        call_ok = wait_for_call(t)
    else:
        call_ok = call(t, remote)

    # Play audio
    if call_ok:
        play_audio(t, audio, length)
    
    # Wait for client to finish call
    if server:
        wait_for(t, "ended", CALL_TIMEOUT)
    else:
        finish_call(t)

    # Close twinkle
    close_twinkle(t)

if __name__ == "__main__":
    # Define usage
    parser = argparse.ArgumentParser(description='',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("ip", type=str,
                        help='The local IP address')
    parser.add_argument('-s', '--server', action='store_true',
                        help='Run in server mode')
    parser.add_argument('-n', '--nat', action='store_true',
                        help='Use a fixed IP NAT')
    parser.add_argument('-r', '--remote', type=str,
                        help='The remotes address')
    parser.add_argument('-a', '--audio', type=str,
                        default=DEFAULT_AUDIO, help='The audio file path to play')
    parser.add_argument('-l', '--length', type=str,
                        default='0', help='The length of the call in seconds')
    parser.add_argument('-p', '--port', type=str,
                        default='{}-{}'.format(PORT_MIN, PORT_MAX), help='The RTP port')
    
    # Get arguments
    args = parser.parse_args()
    server = args.server
    remote = args.remote
    audio = args.audio
    length = float(args.length)
    port = args.port
    ip = args.ip
    nat = args.nat

    if len(port.split('-')) > 1:
        port = random.randrange(int(port.split('-')[0]),
                                int(port.split('-')[1]))
    else:
        port = int(port)
    
    main(server, remote, audio, length, ip, port, nat)
