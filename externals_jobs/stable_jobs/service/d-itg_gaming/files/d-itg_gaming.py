#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2022 Eutelsat
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

"""Sources of the d-itg_gaming.py file"""

__author__ = "Viveris Technologies"
__credits__ = """Contributors:
 * Bastien TAURAN <bastien.tauran@viveris.fr>
"""

import os
import sys
import socket
import shutil
import syslog
import random
import argparse
import ipaddress
import threading
import subprocess
import contextlib
from time import time, sleep

import collect_agent


_FINISHED = threading.Event()


def run_command(cmd, mode="run"):
    try:
        if mode == "Popen":
            p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        else:
            p = subprocess.run(cmd, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error running {} : {}".format(cmd, ex)
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
        shutil.rmtree("/tmp/run{}".format(run_id))
    except FileNotFoundError:
        pass  # Do nothing if the directory does not exist
    s.send("BYE".encode())
    s.close()
    print("Connection closed")


def socket_keep_alive(s):
    """
    Send periodic messages to keep the socket alive
    """
    while not _FINISHED.is_set():
        s.send("HI".encode())
        sleep(5)

def socket_thread(address, port):
    s = socket.socket()
    host = address
    try:
        s.bind((host, port))
    except socket.error as msg:
        print("Socket binding error: " + str(msg) + "\n" + "Retrying...")
    s.listen(1)
    print("Server listening.... on",host,port)

    while True:
        conn, addr = s.accept()
        print("Got connection from", addr)
        run_id = -1

        while True:
            command = conn.recv(1024).decode()
            print("Received command:", command)
            if command == "BYE":
                break
            elif command == "GET_LOG_FILE":
                with open("/tmp/run{}/recv.log".format(run_id),"rb") as f:
                    l = f.read(1024)
                    while (l):
                       conn.send(l)
                       l = f.read(1024)
                sleep(5)
                print("TRANSFERT_FINISHED".encode())
                conn.send("TRANSFERT_FINISHED".encode())
            elif command == "DELETE_FOLDER":
                shutil.rmtree("/tmp/run{}".format(run_id))
            elif "RUN_ID" in command:
                run_id = int(command.split("-")[1])
                print("run_id",run_id)
                os.mkdir("/tmp/run{}".format(run_id))

        conn.close()


def dest(dest_addr, sig_dest_addr, signaling_port, control_port):
    try:
        th = threading.Thread(target=socket_thread, args=(str(sig_dest_addr), control_port))
        th.daemon = True
        th.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()

    try:
        cmd = ['ITGRecv', '-Sp', str(signaling_port)]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as ex:
        message = "Error running ITGRecv : {}".format(ex)
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)

    while True:
        output = process.stdout.readline().decode().strip()
        if not output:
            if process.poll is not None:
                break
            continue
        if output != "Press Ctrl-C to terminate":
            collect_agent.send_log(syslog.LOG_DEBUG, output)
        print(output)

    msg = "ITGRecv has exited with the following return code: {}".format(output)  # Output contains return code
    collect_agent.send_log(syslog.LOG_DEBUG, msg)


def src(src_addr, dest_addr, duration, nb_flows, sig_src_addr, sig_dest_addr, sig_dest_port,
        granularity, nb_runs, waiting_time, starting_port, control_port, game_played):
    with open("/tmp/d-itg_gaming.log", "w") as f:
        for port in range(starting_port, starting_port + nb_flows, 1):
            str_to_write = "-a {} -rp {} -Sda {} -Ssa {} -Sdp {} -t {} -poll {}"\
                .format(dest_addr, port, sig_dest_addr, sig_src_addr, sig_dest_port, int(duration) * 1000, game_played)
            str_to_write += "\n"
            f.write(str_to_write)
            f.flush()

    random.seed()

    for _ in range(1, nb_runs + 1, 1):
        s = socket.socket()
        host = sig_dest_addr if sig_dest_addr else dest_addr
        port = control_port

        s.connect((str(host), port))

        run_id = random.getrandbits(64)
        s.send(("RUN_ID-"+str(run_id)).encode())
        os.mkdir("/tmp/run{}".format(run_id))
        sleep(2)

        # We locally create one log directory per run
        try:
            shutil.rmtree("/tmp/run{}".format(run_id))
        except FileNotFoundError:
            pass  # Do nothing if the directory does not exist
        try:
            os.mkdir("/tmp/run{}".format(run_id))
        except FileExistsError:
            pass  # Do nothing if the directory already exist

        ref_timestamp = collect_agent.now()
        temp_file_name = "{}flows_{}".format(nb_flows, duration)
        local_log_file = "/tmp/run{}/send.log".format(run_id)
        distant_log_file = "/tmp/run{}/recv.log".format(run_id)

        # D-ITG command to send gaming packets, check documentation at http://www.grid.unina.it/software/ITG/manual/
        cmd_send = ["ITGSend",
                    "/tmp/d-itg_gaming.log",
                    "-l", local_log_file,
                    "-x", distant_log_file]

        d_itg_send_ps = run_command(cmd_send, "Popen")

        try:
            _FINISHED.clear()
            th = threading.Thread(target=socket_keep_alive, args=(s,))
            th.daemon = True
            th.start()
        except (KeyboardInterrupt, SystemExit):
            sys.exit()

        d_itg_send_ps.wait()

        _FINISHED.set()

        collect_agent.send_log(syslog.LOG_DEBUG, "Finished run {}".format(run_id))

        # We remotely retrieve logs
        print("Send GET_LOG_FILE")
        s.send("GET_LOG_FILE".encode())
        with open("/tmp/run{}/recv.log".format(run_id), "wb") as f:
            print("file opened")
            while True:
                data = s.recv(1024)
                if "TRANSFERT_FINISHED".encode() in data:
                    break
                f.write(data)
        sleep(2)

        # Thanks to ITGDec, we print all average metrics to file every granularity (in ms)
        cmd_dec = ["ITGDec",
                   "/tmp/run{}/recv.log".format(run_id),
                   "-f", "1",
                   "-c", str(granularity),
                   "/tmp/run{}/combined_stats_{}.dat".format(run_id, temp_file_name)]

        run_command(cmd_dec)

        # We parse the generated log file with average metrics

        # BITRATES (pkt/s):
        # QUAKE3: 144
        # CSa: 24
        # CSi: 24

        if game_played == "Quake3":
            packets_per_second = 144
        elif game_played == "CSa" or game_played == "CSi":
            packets_per_second = 24
        else:
            message = "Error running ITGSend : Game not found for post-processing: {}".format(game_played)
            collect_agent.send_log(syslog.LOG_ERR, message)
            sys.exit(message)

        packets_per_granularity = packets_per_second * float(granularity) / 1000.0
        with open("/tmp/run{}/combined_stats_{}.dat".format(run_id, temp_file_name), "r") as f:
            for line in f:
                stripped_line = line.strip().split()
                timestamp_line = int(float(stripped_line[0]) * 1000) + ref_timestamp
                stat_bitrate = float(stripped_line[1])
                stat_delay = float(stripped_line[2]) * 1000.0
                stat_jitter = float(stripped_line[3]) * 1000.0
                stat_pkt_loss = float(stripped_line[4]) / packets_per_granularity
                # We build the dict to send with the collect agent
                statistics = {
                    "bitrate (Kbits/s)": stat_bitrate,
                    "delay (ms)": stat_delay,
                    "jitter (ms)": stat_jitter,
                    "packet_loss (%)": stat_pkt_loss
                }

                collect_agent.send_stat(timestamp_line, **statistics)

        # We purge D-ITG logs
        clean(s, run_id)
        sleep(waiting_time)


if __name__ == "__main__":
    with collect_agent.use_configuration("/opt/openbach/agent/jobs/d-itg_gaming/d-itg_gaming_rstats_filter.conf"):
        parser = argparse.ArgumentParser(
                description="Generate gaming traffic with D-ITG software. This job generate gaming traffic for "
                "Quake3 and Counter Strike unidirectionnaly between a source and a destination.",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        subparsers = parser.add_subparsers(
            title="Subcommand mode",
            help="Choose the iperf3 mode (source mode or destination mode)",
            dest="mode")
        subparsers.required = True

        # Only source parameters
        parser_source = subparsers.add_parser("source", help="Run in source mode")
        parser_source.add_argument("src_addr", type=ipaddress.ip_address,
                            help="The IPv4 address generating gaming traffic")
        parser_source.add_argument("dest_addr", type=ipaddress.ip_address,
                            help="The IPv4 address receiveing gaming traffic")
        parser_source.add_argument("duration", type=int, 
                            help="The duration of one gaming session in seconds")
        parser_source.add_argument("-f", "--nb_flows", type=int, default=1,
                            help="The number of parallel gaming sessions to start")
        parser_source.add_argument("-Ssa", "--sig_src_addr", type=ipaddress.ip_address, default=None,
                            help="The source address for the signaling channel")
        parser_source.add_argument("-Ssd", "--sig_dest_addr", type=ipaddress.ip_address, default=None,
                            help="The destination address for the signaling channel")
        parser_source.add_argument("-Sdp", "--sig_dest_port", type=int, default=9100,
                            help="Set the destination port for the signaling channel. Default: 9100")
        parser_source.add_argument("-g", "--granularity", type=int, default=1000,
                            help="Statistics granularity in milliseconds")
        parser_source.add_argument("-n", "--nb_runs", type=int, default=1,
                            help="The number of runs to perform for each gaming session")
        parser_source.add_argument("-w", "--waiting_time", type=int, default=0,
                            help="The number of seconds to wait between two ")
        parser_source.add_argument("-p", "--starting_port", type=int, default=10000,
                            help="The starting port to emit gaming sessions. Each session is emitted on a different port "
                                 "(e.g., 10000, 10001, etc.).")
        parser_source.add_argument("-cp", "--control_port", type=int, default=50000,
                            help="The port used on the sender side to send and receive OpenBACH commands from the client."
                                 "Should be the same on the destination side.  Default: 50000.")
        parser_source.add_argument("-G", "--game_played", type=str, choices=["CSa", "CSi", "Quake3"], default="Quake3",
                            help="The game traffic to send. Possible values are: CSa (Counter Strike active), CSi (Counter Strike idle), Quake3.  Default: Quake3.")

        # Only destination parameters
        parser_destination = subparsers.add_parser("destination", help="Run in destination mode")
        parser_destination.add_argument("dest_addr", type=ipaddress.ip_address,
                            help="The IPv4 address receiveing gaming traffic")
        parser_destination.add_argument("-Ssd", "--sig_dest_addr", type=ipaddress.ip_address, default=None,
                            help="The destination address for the signaling channel")
        parser_destination.add_argument("-cp", "--control_port", type=int, default=50000,
                            help="The port used on the sender side to send and receive OpenBACH commands from the client."
                                 "Should be the same on the destination side.  Default: 50000.")
        parser_destination.add_argument("-sp", "--signaling_port", type=int, default=9100,
                            help="Signaling channel port number. Default: 9100.")

        parser_source.set_defaults(function=src)
        parser_destination.set_defaults(function=dest)

        # Get args and call the appropriate function
        args = vars(parser.parse_args())
        main = args.pop("function")

        if args["mode"] == "source" and (args["sig_src_addr"] is None or args["sig_dest_addr"] is None):
            args["sig_src_addr"] = args["src_addr"]
            args["sig_dest_addr"] = args["dest_addr"]

        if args["mode"] == "destination" and args["sig_dest_addr"] is None:
            args["sig_dest_addr"] = args["dest_addr"]

        args.pop("mode")

        main(**args)
