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


"""Sources of the Job ftp"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Matthieu PETROU <matthieu.petrou@toulouse.viveris.com>

'''

import os
import time
import random
import syslog
import pathlib
import argparse
from sys import exit
from ftplib import FTP

import collect_agent


class Stat_data:
    block_len = 0
    total_block_len = 0
    timer = 0

def handleUpload(block, stat_data):
    timestamp = time.time() * 1000
    stat_data.block_len += len(block)
    if timestamp - stat_data.timer >= 1000:
        collect_agent.send_stat(int(timestamp), throughput_upload  = 
            (stat_data.block_len*8000/(timestamp - stat_data.timer)))
        stat_data.timer = timestamp
        stat_data.total_block_len += stat_data.block_len
        stat_data.block_len = 0

def handleDownload(block, stat_data, file_download):
    timestamp = time.time() * 1000
    stat_data.block_len += len(block)
    file_download.write(block)
    if timestamp - stat_data.timer >= 1000:
        collect_agent.send_stat(int(timestamp), throughput_download  = 
            (stat_data.block_len*8000/(timestamp - stat_data.timer)))
        stat_data.timer = timestamp
        stat_data.total_block_len += stat_data.block_len
        stat_data.block_len = 0

def generate_path():
    #generate a random directory
    path = ''
    while len(path) < 10:
        path += random.choice('azertyuiopqsdfghjklmwxcvbn')
    return path + '/'

def init_ftp(server_ip, port, user, password):
    stat_data = Stat_data()
    ftp = FTP()
    ftp.connect(server_ip,port)
    ftp.login(user,password)
    return ftp, stat_data

def format_path(path, root=''):
    _root = pathlib.Path.cwd().root
    absolute_path = os.path.abspath(os.path.join(_root, path))
    if root:
        return os.path.join(root, os.path.relpath(absolute_path, _root))
    else:
        return os.path.relpath(absolute_path, _root)

def download(server_ip, port, user, password, blocksize, file_path):
    #Open session with FTP Server
    ftp, stat_data = init_ftp(server_ip, port, user, password)
    #Create local download directory
    dl_dir = '/srv/' + generate_path()
    os.mkdir(dl_dir)
    #Download the file
    file_name = file_path.split('/')[-1]
    file_download = open(dl_dir + file_name, 'wb')
    stat_data.timer = time.time() * 1000
    ftp.retrbinary('RETR ' + file_path, lambda block: handleDownload(block, stat_data, file_download), blocksize)
    #Collect stats
    timestamp = time.time() * 1000
    stat_data.total_block_len += stat_data.block_len
    collect_agent.send_stat(int(timestamp), throughput_download = 
        (stat_data.block_len*8000/(timestamp-stat_data.timer)))
    collect_agent.send_stat(int(timestamp), total_blocksize_downloaded = 
        (stat_data.total_block_len * 8))
    ftp.close()
    #Remove temporary files
    os.remove(dl_dir + file_name)
    os.system('rm -r ' + dl_dir)

def upload(server_ip, port, user, password, blocksize, file_path):
    #Open session with FTP Server
    ftp, stat_data = init_ftp(server_ip, port, user, password)
    #Create storage directory on server
    srv_store_dir = generate_path()
    ftp.mkd(srv_store_dir)
    #Upload the file 
    file_name = file_path.split('/')[-1]
    file_upload = open(file_path, 'rb')
    stat_data.timer = time.time() * 1000
    ftp.storbinary('STOR ' + srv_store_dir + file_name, file_upload,
            blocksize, lambda block: handleUpload(block, stat_data))
    #Collect stats
    timestamp = time.time() * 1000
    stat_data.total_block_len += stat_data.block_len
    collect_agent.send_stat(int(timestamp), throughput_upload = 
        (stat_data.block_len*8000/(timestamp-stat_data.timer)))
    collect_agent.send_stat(int(timestamp), total_blocksize_uploaded = 
        (stat_data.total_block_len * 8))
    ftp.close()

def build_parser():
    parser = argparse.ArgumentParser(description='FTP client Parser')
    parser.add_argument('server_ip', help='Server IP', type=str)
    parser.add_argument('port', help='Server port', type=int)
    parser.add_argument('mode', type=str, choices=['upload', 'download'],
        help='Set the client mode: upload or download')
    parser.add_argument('--user', '-u', type=str, default='openbach',
        help='Authorized User (default openbach)')
    parser.add_argument('--password', '-p', type=str, default='openbach',
        help="Authorized User's Password (default openbach)")
    parser.add_argument('--blocksize', '-b', type=int, default=8192,
        help='Set maximum chunk size  (default=8192)')

    #Sub-commands functionnality to choose file
    subparsers = parser.add_subparsers(title='File existing or user own file', dest='file',
        help='Choose between a pre-existing file of the job or your own file')
    subparsers.required=True
    parser_existing_file=subparsers.add_parser('existing', help='existing file of the job')
    parser_existing_file.add_argument(dest='file_choice', type=str,
        choices=['500K_file.txt', '1M_file.txt', '10M_file.txt',
        '100M_file.txt'],
        help='Choose a pre-existing file')
    parser_own_file = subparsers.add_parser('own', help='your own file')
    parser_own_file.add_argument(dest='own_file', type=str,
        help = 'Give the file path and name, consider /srv/ as the home directory')
    return parser

if __name__ == '__main__':
    #parse the command
    args = build_parser().parse_args()

    #Open the register collect
    success = collect_agent.register_collect(
            '/opt/openbach/agent/jobs/ftp_clt/'
            'ftp_clt_rstats_filter.conf')
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    #set file path
    if args.file == 'existing':
        file_path = args.file_choice
    elif args.file == 'own':
        file_path = args.own_file
    else:
        message = 'No file chosen'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    #Depending on the mode, call the dedicated function
    if args.mode == 'upload':
        file_path = format_path(file_path, '/srv/')
        upload(args.server_ip, args.port, args.user, args.password, args.blocksize, file_path)
    elif args.mode == 'download':
        file_path = format_path(file_path)
        download(args.server_ip, args.port, args.user, args.password, args.blocksize, file_path)
    else:
        message = 'No mode chosen'
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)

