#!/usr/bin/env python3

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2023 CNES
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
import random
import syslog
import pathlib
import argparse
from sys import exit
from ftplib import FTP

import collect_agent


class StatData:
    block_len = 0
    total_block_len = 0
    timer = 0


def handleUpload(block, stat_data):
    timestamp = collect_agent.now()
    stat_data.block_len += len(block)
    if timestamp - stat_data.timer >= 1000:
        throughput = stat_data.block_len*8000 / (timestamp - stat_data.timer)
        collect_agent.send_stat(timestamp, throughput_upload=throughput)
        stat_data.timer = timestamp
        stat_data.total_block_len += stat_data.block_len
        stat_data.block_len = 0


def handleDownload(block, stat_data, file_download):
    timestamp = collect_agent.now()
    stat_data.block_len += len(block)
    file_download.write(block)
    if timestamp - stat_data.timer >= 1000:
        throughput = stat_data.block_len*8000 / (timestamp - stat_data.timer)
        collect_agent.send_stat(timestamp, throughput_download=throughput)
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
    stat_data = StatData()
    ftp = FTP()
    ftp.connect(server_ip,port)
    ftp.login(user,password)
    return ftp, stat_data


def format_path(path, root=''):
    _root = pathlib.Path.cwd().root
    relative_path = pathlib.Path(_root, path).resolve().relative_to(_root)
    if root:
        return pathlib.Path(root, relative_path)
    else:
        return relative_path


def download(server_ip, port, user, password, blocksize, file_path):
    # Open session with FTP Server
    ftp, stat_data = init_ftp(server_ip, port, user, password)
    # Create local download directory
    dl_dir = '/srv/' + generate_path()
    os.mkdir(dl_dir)
    # Download the file
    file_name = file_path.name
    stat_data.timer = collect_agent.now()
    try:
        with open(dl_dir + file_name, 'rb') as file_download:
            ftp.retrbinary(
                    'RETR ' + file_path.as_posix(),
                    lambda block: handleDownload(block, stat_data, file_download),
                    blocksize)
    except Exception as ex:
        message = 'Error downloading file : {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)
    # Collect stats
    timestamp = collect_agent.now()
    stat_data.total_block_len += stat_data.block_len
    throuhgput = stat_data.block_len*8000 / (timestamp - stat_data.timer)
    collect_agent.send_stat(timestamp, throughput_download=throuhgput)
    collect_agent.send_stat(timestamp, total_blocksize_downloaded=(stat_data.total_block_len * 8))
    ftp.close()
    # Remove temporary files
    os.remove(dl_dir + file_name)
    os.system('rm -r ' + dl_dir)


def upload(server_ip, port, user, password, blocksize, file_path):
    # Open session with FTP Server
    ftp, stat_data = init_ftp(server_ip, port, user, password)
    # Create storage directory on server
    srv_store_dir = generate_path()
    ftp.mkd(srv_store_dir)
    # Upload the file 
    file_name = file_path.name
    stat_data.timer = collect_agent.now()
    try:
        with file_path.open('rb') as file_upload:
            ftp.storbinary(
                    'STOR ' + srv_store_dir + file_name,
                    file_upload, blocksize,
                    lambda block: handleUpload(block, stat_data))
    except Exception as ex:
        message = 'Error uploading file : {}'.format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        exit(message)
    # Collect stats
    timestamp = collect_agent.now()
    stat_data.total_block_len += stat_data.block_len
    thoughput = stat_data.block_len*8000 / (timestamp - stat_data.timer)
    collect_agent.send_stat(timestamp, throughput_upload=throuput)
    collect_agent.send_stat(timestamp, total_blocksize_uploaded=(stat_data.total_block_len * 8))
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
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/ftp_clt/ftp_clt_rstats_filter.conf'):
        #parse the command
        args = build_parser().parse_args()
    
        #set file path
        if args.file == 'existing':
            file_path = args.file_choice
        elif args.file == 'own':
            file_path = args.own_file
        else:
            message = 'No file chosen'
            collect_agent.send_log(syslog.LOG_ERR, message)
            exit(message)
    
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
