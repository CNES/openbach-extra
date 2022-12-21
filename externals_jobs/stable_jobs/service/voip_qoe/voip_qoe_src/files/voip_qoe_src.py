#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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

import sys
import yaml
import socket
import shutil
import syslog
import random
import tempfile
import argparse
import ipaddress
import threading
import subprocess
from time import sleep
from pathlib import Path

import collect_agent
from codec import CodecConstants
from compute_mos import compute_r_value, compute_mos_value


job_dir = Path('/opt/openbach/agent/jobs/voip_qoe_src')
dest_job_dir = job_dir.parent / 'voip_qoe_dest'

FINISHED = threading.Event()


def build_parser():
    """Method used to validate the parameters supplied to the program

    :return: an object containing required/optional arguments with their values
    :rtype: object
    """
    parser = argparse.ArgumentParser(
            description='Start a sender (source) component to measure QoE of one or '
            'many VoIP sessions generated with D-ITG software',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            'src_addr', type=ipaddress.ip_address,
            help='The source IPv4 address to use for the VoIP session')
    parser.add_argument(
            'dest_addr', type=ipaddress.ip_address,
            help='The destination IPv4 address to use for the VoIP session')
    parser.add_argument(
            'codec', choices=['G.711.1', 'G.711.2', 'G.723.1', 'G.729.2', 'G.729.3'],
            help="The codec to use to perform the VoIP sessions")
    parser.add_argument(
            'duration', type=int,
            help='The duration of one VoIP session in seconds')
    parser.add_argument(
            '-f', '--nb_flows',
            type=int, default=1,
            help='The number of parallel VoIP session to start')
    parser.add_argument(
            '-Ssa', '--sig_src_addr',
            type=ipaddress.ip_address,
            help='The source address for the signaling channel')
    parser.add_argument(
            '-Ssd', '--sig_dest_addr',
            type=ipaddress.ip_address,
            help='The destination address for the signaling channel')
    parser.add_argument(
            '-Sdp', '--signaling_dest_port',
            type=int, default=9000,
            help='Set the destination port for the signaling channel')
    parser.add_argument(
            '-j', '--use_jitter',
            action='store_true',
            help='Whether or not to convert jitter into delay for the MOS computation')
    parser.add_argument(
            '-v', '--vad',
            action='store_true',
            help='Whether or not to use the Voice Activity Detection (VAD) option in ITGSend')
    parser.add_argument(
            '-g', '--granularity',
            type=int, default=1000,
            help='Statistics granularity in milliseconds')
    parser.add_argument(
            '-n', '--nb_runs',
            type=int, default=1,
            help='The number of runs to perform for each VoIP session')
    parser.add_argument(
            '-w', '--waiting_time',
            type=int, default=0,
            help='The number of seconds to wait between two sessions')
    parser.add_argument(
            '-p', '--starting_port',
            type=int, default=10000,
            help='The starting port to emit VoIP sessions. Each session is emitted '
            'on a different port (e.g., 10000, 10001, etc.).')
    parser.add_argument(
            '-cp', '--control_port',
            type=int, default=50000,
            help='The port used on the sender side to send and receive OpenBACH commands from '
            'the client. Should be the same on the destination side. Default: 50000.')
    parser.add_argument(
            '-pt', '--protocol',
            default='RTP', choices=['RTP', 'CRTP'],
            help='The protocol to use to perform the VoIP sessions')

    return parser


def run_command(*cmd, wait_for_completion=True):
    runner = subprocess.run if wait_for_completion else subprocess.Popen
    try:
        return runner(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = 'Error running {} : {}'.format(cmd, ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


def socket_keep_alive(s):
    """Send periodic messages to keep the socket alive"""
    while not FINISHED.is_set():
        s.send(b'HI')
        sleep(5)


def main(config, args):
    """Main method

    :param config: a dict object that contain the parameters of the 'internal_config.yml' file
    :type config: dict
    :param args: the parsed arguments returned by the parser
    :type args: object
    :return: nothing
    """
    random.seed()
    packets_per_granularity = config['CODEC_BITRATES'][args.codec] * args.granularity / 1000.0
    codec = CodecConstants(
            collect_agent=collect_agent,
            etc_dir_path=job_dir.joinpath('etc').as_posix(),
            codec_name=args.codec)

    # We write into a temp file all VoIP flows to be sent
    with tempfile.NamedTemporaryFile('w', dir=job_dir, suffix=config['FILE_TEMP_FLOWS']) as flows:
        for port in range(args.starting_port, args.starting_port + args.nb_flows):
            print('-a', args.dest_addr,
                  '-rp', port,
                  '-Sda', args.sig_dest_addr,
                  '-Ssa', args.sig_src_addr,
                  '-Sdp', args.signaling_dest_port,
                  '-t', int(args.duration * 1000),
                  '-poll', 'VoIP',
                  '-x', args.codec,
                  '-h', args.protocol,
                  end='', file=flows)
            print(' -VAD' if args.vad else '', file=flows, flush=True)

        for _ in range(args.nb_runs):
            with socket.socket() as s:
                s.connect((str(args.sig_dest_addr), args.control_port))

                run_id = random.getrandbits(64)
                s.send(b'RUN_ID-' + str(run_id).encode())

                run = job_dir / 'logs' / 'run{}'.format(run_id)
                shutil.rmtree(run, ignore_errors=True)
                run.mkdir(parents=True, exist_ok=True)
                sleep(2)

                ref_timestamp = collect_agent.now()
                temp_file_name = "{}flows_{}_{}_{}s".format(args.nb_flows, args.codec, args.protocol, args.duration)
                local_log_file = run / 'send.log'
                distant_log_file = dest_job_dir / run.relative_to(job_dir) / 'recv.log'

                # D-ITG command to send VoIP packets
                # check documentation at http://www.grid.unina.it/software/ITG/manual/
                d_itg_send_ps = run_command(
                        'ITGSend', flows.name,
                        '-l', local_log_file.as_posix(),
                        '-x', distant_log_file.as_posix(),
                        wait_for_completion=False)

                FINISHED.clear()
                th = threading.Thread(target=socket_keep_alive, args=(s,))
                try:
                    th.start()
                    d_itg_send_ps.wait()
                finally:
                    FINISHED.set()
                    th.join()

                collect_agent.send_log(syslog.LOG_DEBUG, "Finished run {}".format(run_id))

                # We remotely retrieve logs
                s.send(b'GET_LOG_FILE')
                received_log_file = local_log_file.parent / 'recv.log'
                with received_log_file.open('wb') as f:
                    while True:
                        data = s.recv(1024)
                        index = data.find(b'TRANSFERT_FINISHED')
                        if index >= 0:
                            f.write(data[:index])
                            break
                        f.write(data)
                sleep(2)

                # Thanks to ITGDec, we print all average metrics to file every args.granularity (in ms)
                metrics_file = local_log_file.parent / 'combined_stats_{}.dat'.format(temp_file_name)
                run_command(
                        'ITGDec',
                        received_log_file.as_posix(),
                        '-f', '1', '-c', str(args.granularity),
                        metrics_file.as_posix())

                # We parse the generated log file with average metrics
                with metrics_file.open('r') as f:
                    for line in f:
                        timestamp, bitrate, delay, jitter, pkt_loss, *_ = map(float, line.split())
                        timestamp = int(timestamp * 1000) + ref_timestamp
                        delay *= 1000
                        jitter *= 1000
                        pkt_loss /= packets_per_granularity
                        R_factor = compute_r_value(codec, delay, delay, pkt_loss, jitter, args.use_jitter)
                        # We build the dict to send with the collect agent
                        statistics = {
                            'instant_mos': compute_mos_value(R_factor),
                            'instant_r_factor': R_factor,
                            'bitrate (Kbits/s)': bitrate,
                            'delay (ms)': delay,
                            'jitter (ms)': jitter,
                            'packet_loss (%)': pkt_loss
                        }
                        collect_agent.send_stat(timestamp, **statistics)

                # We purge D-ITG logs
                s.send(b'DELETE_FOLDER')
                sleep(2)
                shutil.rmtree(run, ignore_errors=True)
                s.send(b'BYE')

            sleep(args.waiting_time)


if __name__ == "__main__":
    with collect_agent.use_configuration(job_dir.joinpath('voip_qoe_dest_rstats_filter.conf').as_posix()):
        # Internal configuration loading
        with job_dir.joinpath('etc', 'internal_config.yml').open() as stream:
            config = yaml.safe_load(stream)
    
        # Argument parsing
        args = build_parser().parse_args()
    
        if args.sig_src_addr is None:
            args.sig_src_addr = args.src_addr
        if args.sig_dest_addr is None:
            args.sig_dest_addr = args.dest_addr
    
        main(config, args)
