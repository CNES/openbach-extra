#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2020 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.

"""Sources of the voip_qoe_src.py file"""

__author__ = 'Antoine AUGER'
__credits__ = '''Contributors:
 * Antoine AUGER <antoine.auger@tesa.prd.fr>
 * Bastien TAURAN <bastien.tauran@viveris.fr>
'''

import os
import yaml
import socket
import shutil
import syslog
import random
import argparse
import ipaddress
import threading
import subprocess
from time import time, sleep
from codec import CodecConstants
from compute_mos import compute_r_value, compute_mos_value

import collect_agent

job_dir = '/opt/openbach/agent/jobs/voip_qoe_src'
dest_job_dir = '/opt/openbach/agent/jobs/voip_qoe_dest'

_FINISHED = False


def connect_to_collect_agent():
    conffile = '{}/voip_qoe_dest_rstats_filter.conf'.format(job_dir)
    success = collect_agent.register_collect(conffile)
    if not success:
        message = 'ERROR connecting to collect-agent'
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


def get_timestamp():
    """
    To get a simple timestamp

    :return: the current time in milliseconds
    :rtype: int
    """
    return int(round(time() * 1000))


def build_parser():
    """
    Method used to validate the parameters supplied to the program

    :return: an object containing required/optional arguments with their values
    :rtype: object
    """
    parser = argparse.ArgumentParser(description='Start a sender (source) component to measure QoE of one or '
                                                 'many VoIP sessions generated with D-ITG software',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('src_addr', type=ipaddress.ip_address,
                        help='The source IPv4 address to use for the VoIP session')
    parser.add_argument('dest_addr', type=ipaddress.ip_address,
                        help='The destination IPv4 address to use for the VoIP session')
    parser.add_argument('codec', type=str, choices=['G.711.1', 'G.711.2', 'G.723.1', 'G.729.2', 'G.729.3'],
                        help="The codec to use to perform the VoIP sessions")
    parser.add_argument('duration', type=int, 
                        help='The duration of one VoIP session in seconds')
    parser.add_argument('-f', '--nb_flows', type=int, default=1,
                        help='The number of parallel VoIP session to start')
    parser.add_argument('-Ssa', '--sig_src_addr', type=ipaddress.ip_address, default=None,
                        help='The source address for the signaling channel')
    parser.add_argument('-Ssd', '--sig_dest_addr', type=ipaddress.ip_address, default=None,
                        help='The destination address for the signaling channel')
    parser.add_argument('-j', '--use_jitter', action='store_true',
                        help='Whether or not to convert jitter into delay for the MOS computation')
    parser.add_argument('-v', '--vad', action='store_true',
                        help='Whether or not to use the Voice Activity Detection (VAD) option in ITGSend')
    parser.add_argument('-g', '--granularity', type=int, default=1000,
                        help='Statistics granularity in milliseconds')
    parser.add_argument('-n', '--nb_runs', type=int, default=1,
                        help='The number of runs to perform for each VoIP session')
    parser.add_argument('-w', '--waiting_time', type=int, default=0,
                        help='The number of seconds to wait between two ')
    parser.add_argument('-p', '--starting_port', type=int, default=10000,
                        help='The starting port to emit VoIP sessions. Each session is emitted on a different port '
                             '(e.g., 10000, 10001, etc.).')
    parser.add_argument('-cp', '--control_port', type=int, default=50000,
                        help='The port used on the sender side to send and receive OpenBACH commands from the client.'
                             'Should be the same on the destination side.  Default: 50000.')
    parser.add_argument('-pt', '--protocol', type=str, default='RTP', choices=['RTP', 'CRTP'],
                        help='The protocol to use to perform the VoIP sessions')
    return parser


def run_command(cmd, mode='run'):
    try:
        if mode == 'Popen':
            p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        else:
            p = subprocess.run(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = 'Error running {} : {}'.format(cmd, ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    return p


def clean(s, run_id):
    """
    Removes temp folders on both sides before exiting job
    """
    s.send("DELETE_FOLDER".encode())
    sleep(2)
    try:
        shutil.rmtree('{}/logs/run{}'.format(job_dir, run_id))
    except FileNotFoundError:
        pass  # Do nothing if the directory does not exist
    s.send("BYE".encode())
    s.close()
    print('Connection closed')


def socket_keep_alive(s):
    """
    Send periodic messages to keep the socket alive
    """
    while not _FINISHED:
        s.send("HI".encode())
        sleep(5)


def main(config, args):
    """
    Main method

    :param config: a dict object that contain the parameters of the 'internal_config.yml' file
    :type config: dict
    :param args: the parsed arguments returned by the parser
    :type args: object
    :return: nothing
    """

    global _FINISHED

    connect_to_collect_agent()

    # We write into a temp file all VoIP flows to be sent
    #with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), config['FILE_TEMP_FLOWS']), "w") as f:
    with open('{}/{}'.format(job_dir, config['FILE_TEMP_FLOWS']), "w") as f:
        for port in range(args.starting_port, args.starting_port + args.nb_flows, 1):
            str_to_write = "-a {} -rp {} -Sda {} -Ssa {} -t {} -poll VoIP -x {} -h {}"\
                .format(args.dest_addr, port, args.sig_dest_addr, args.sig_src_addr, int(args.duration) * 1000,
                        args.codec, args.protocol)
            if args.vad:
                str_to_write += " -VAD"
            str_to_write += "\n"
            f.write(str_to_write)
            f.flush()

    random.seed()

    for _ in range(1, args.nb_runs + 1, 1):
        s = socket.socket()
        host = args.sig_dest_addr if args.sig_dest_addr else args.dest_addr
        port = args.control_port

        s.connect((str(host), port))

        run_id = random.getrandbits(64)
        s.send(("RUN_ID-"+str(run_id)).encode())
        os.mkdir('{}/logs/run{}'.format(job_dir, run_id))
        sleep(2)

        # We locally create one log directory per run
        try:
            shutil.rmtree('{}/logs/run{}'.format(job_dir, run_id))
        except FileNotFoundError:
            pass  # Do nothing if the directory does not exist
        try:
            os.mkdir('{}/logs/run{}'.format(job_dir, run_id))
        except FileExistsError:
            pass  # Do nothing if the directory already exist

        ref_timestamp = get_timestamp()
        temp_file_name = "{}flows_{}_{}_{}s".format(args.nb_flows, args.codec, args.protocol, args.duration)
        local_log_file = '{}/logs/run{}/send.log'.format(job_dir, run_id)
        distant_log_file = '{}/logs/run{}/recv.log'.format(dest_job_dir, run_id)

        # D-ITG command to send VoIP packets, check documentation at http://www.grid.unina.it/software/ITG/manual/
        cmd_send = ['ITGSend',
                    '{}/{}'.format(job_dir, config['FILE_TEMP_FLOWS']),
                    '-l', local_log_file,
                    '-x', distant_log_file]

        d_itg_send_ps = run_command(cmd_send, 'Popen')

        try:
            _FINISHED = False
            th = threading.Thread(target=socket_keep_alive, args=(s,))
            th.daemon = True
            th.start()
        except (KeyboardInterrupt, SystemExit):
            exit()

        d_itg_send_ps.wait()

        _FINISHED = True

        collect_agent.send_log(syslog.LOG_DEBUG, "Finished run {}".format(run_id))

        # We remotely retrieve logs
        s.send("GET_LOG_FILE".encode())
        with open('{}/logs/run{}/recv.log'.format(job_dir, run_id), 'wb') as f:
            print('file opened')
            while True:
                data = s.recv(1024)
                if "TRANSFERT_FINISHED".encode() in data:
                    break
                f.write(data)
        sleep(2)

        # Thanks to ITGDec, we print all average metrics to file every args.granularity (in ms)
        cmd_dec = ['ITGDec',
                   '{}/logs/run{}/recv.log'.format(job_dir, run_id),
                   '-f', '1',
                   '-c', str(args.granularity),
                   '{}/logs/run{}/combined_stats_{}.dat'.format(job_dir, run_id, temp_file_name)]

        run_command(cmd_dec)

        # We parse the generated log file with average metrics
        packets_per_granularity = float(config['CODEC_BITRATES'][args.codec]) * float(args.granularity) / 1000.0
        with open('{}/logs/run{}/combined_stats_{}.dat'.format(job_dir, run_id, temp_file_name), "r") as f:
            for line in f:
                stripped_line = line.strip().split()
                timestamp_line = int(float(stripped_line[0]) * 1000) + ref_timestamp
                stat_bitrate = float(stripped_line[1])
                stat_delay = float(stripped_line[2]) * 1000.0
                stat_jitter = float(stripped_line[3]) * 1000.0
                stat_pkt_loss = float(stripped_line[4]) / packets_per_granularity
                my_codec = CodecConstants(collect_agent=collect_agent,
                                          etc_dir_path='{}/etc'.format(job_dir),
                                          codec_name=args.codec)
                if args.use_jitter:
                    stat_r_factor = compute_r_value(my_codec, stat_delay, stat_delay, stat_pkt_loss, stat_jitter,
                                                    use_jitter=True)
                else:
                    stat_r_factor = compute_r_value(my_codec, stat_delay, stat_delay, stat_pkt_loss, stat_jitter,
                                                    use_jitter=False)
                stat_mos = compute_mos_value(stat_r_factor)
                # We build the dict to send with the collect agent
                statistics = {
                    'instant_mos': stat_mos,
                    'instant_r_factor': stat_r_factor,
                    'bitrate (Kbits/s)': stat_bitrate,
                    'delay (ms)': stat_delay,
                    'jitter (ms)': stat_jitter,
                    'packet_loss (%)': stat_pkt_loss
                }
                collect_agent.send_stat(timestamp_line, **statistics)

        # We purge D-ITG logs
        clean(s, run_id)
        sleep(args.waiting_time)


if __name__ == "__main__":
    # Internal configuration loading
    config = yaml.safe_load(open('{}/etc/internal_config.yml'.format(job_dir)))

    # Argument parsing
    args = build_parser().parse_args()

    if args.sig_src_addr is None or args.sig_dest_addr is None:
        args.sig_src_addr = args.src_addr
        args.sig_dest_addr = args.dest_addr

    main(config, args)
