#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016−2019 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.


"""Sources of the Job netcat"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
 * Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>
'''


import sys
import time
import syslog
import argparse
import subprocess

import collect_agent
import re
import os


TMP_FILENAME='/tmp/socat.out'

def get_file_size(name):
    if len(name.split('/')) > 1:
        return 0
    
    size, unit = re.search("([0-9]*)([a-zA-Z]*)", name).groups()
    
    try:
        size = int(size)
    except ValueError:
        return 0
    
    if 'm' in unit.lower():
        size = size * 1024 * 1024
    elif 'k' in unit.lower():
        size = size * 1024
    return size
    

def main(server, dest, port, fn, measure_t, create_f):
    # Connect to collect agent
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/socat/'
            'socat_rstats_filter.conf')
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)
    collect_agent.send_log(syslog.LOG_DEBUG, "Starting job socat")

    # Verify arguments
    if server:
        if not port:
            message = "ERROR missing port parameter"
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)
        if not fn:
            message = "ERROR missing file parameter"
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)
    else:
        if not dest:
            message = "ERROR missing dest parameter"
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)
        if not port:
            message = "ERROR missing port parameter"
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)

    # Create file if necessary
    if server and create_f:
        # get file size from name
        size = get_file_size(fn)
        if not size:
            message = "ERROR wrong file name"
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)
        cmd = ['dd', 'if=/dev/zero', 'of={}'.format(TMP_FILENAME),
               'bs=1', 'count={}'.format(size)]
        p = subprocess.run(cmd)
        if p.returncode != 0:
            message = "WARNING wrong return code when creating file"
            collect_agent.send_log(syslog.LOG_WARNING, message)

    if server:
        cmd = ['socat', 'TCP-LISTEN:{},reuseaddr,fork,crlf'.format(port),
               'SYSTEM:"cat {}"'.format(TMP_FILENAME if create_f else fn)]
    else:
        cmd = ['socat', '-u', 'TCP:{}:{}'.format(dest, port),
               'OPEN:{},creat,trunc'.format(TMP_FILENAME)]
        
    if measure_t:
        cmd = ['/usr/bin/time', '-f', '%e', '--quiet'] + cmd
    try:
        p = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                          stdin=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    except Exception as ex:
        message = "ERROR executing socat: {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(mesage)
    
    # Check if file is correct
    all_ok = True
    if not server:
        size = get_file_size(fn)
        if size and size != os.path.getsize(TMP_FILENAME):
            collect_agent.send_log(syslog.LOG_WARNING, "Wrong file size:"
                                   " expecting {}, got {}".format(size,
                                                                os.path.getsize(TMP_FILENAME)))
            all_ok = False
    
    # Delete file 
    cmd = ['rm', TMP_FILENAME]
    r = subprocess.run(cmd)
    
    # Send statistics
    statistics = {}
    timestamp = int(round(time.time() * 1000))
    if not measure_t:
        return
    if p.returncode == 0 and all_ok:
        timestamp = int(time.time() * 1000)
        stderr = p.stderr
        try:
            duration = float(stderr)
        except ValueError:
            collect_agent.send_log(
                    syslog.LOG_ERR,
                    'ERROR: cannot convert output to duration '
                    'value: {}'.format(stderr))
        else:
            try:
                collect_agent.send_stat(timestamp, duration=duration)
            except Exception as ex:
                collect_agent.send_log(
                        syslog.LOG_ERR,
                        'ERROR sending stat: {}'.format(ex))
    elif p.returncode:
        collect_agent.send_log(
                syslog.LOG_ERR,
                'ERROR: return code {}: {}'
                .format(p.returncode, p.stderr))


if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # TODO: add mutual exclusivities
    parser.add_argument('-s', '--server', action='store_true',
                        help='Launch on server mode')
    parser.add_argument('-d', '--dest', type=str, default='',
                        help='The dest IP address')
    parser.add_argument('-f', '--file', type=str, default='',
                        help='The output file path, or size if create file')#req server
    parser.add_argument('-t', '--time', action='store_true',
                        help='Measure the duration of the process') # opt client
    parser.add_argument('-c', '--create', action='store_true',
                        help='Create the file') # opt server
    
    parser.add_argument('-p', '--port', type=int, default=0,
                        help='The TCP port number')

    # get args
    args = parser.parse_args()
    server = args.server
    dest = args.dest
    port = args.port
    fn = args.file
    measure_t = args.time
    create_f = args.create

    main(server, dest, port, fn, measure_t, create_f)
