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


"""Sources of the Job ip_scheduler"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Bastien TAURAN <bastien.tauran@toulouse.viveris.com>

'''

import json
import syslog
import argparse
import subprocess
from collections import OrderedDict

import collect_agent


def run_command(cmd):
    p = subprocess.run(cmd, stderr=subprocess.PIPE)
    if p.returncode:
        collect_agent.send_log(syslog.LOG_ERR,
                "Error when executing command '{}': '{}'".format(
                    ' '.join(cmd), p.stderr.decode()))
    return p.returncode


def convert_extension(n):
    try:
        n = float(n)
        return int(n)
    except ValueError:
        val,ext = n[:-1],n[-1]
        try:
            val = float(val)
            if ext in "kK":
                return int(1000*val)
            if ext in "mM":
                return int(1000000*val)
            return -1
        except ValueError:
            return -1


def to_kilo(n):
    return str(n//1000)+"k"


def create_commands(data,interface):
    qdisc_file = open("/tmp/qdisc_generated.sh","w")

    # Add AQMs at the end to avoid id conflicts
    AQMs = []

    # Rate of whole transmission (sum of trunks rates)
    global_rate = 0
    global_rates = {}
    for trk,rate in data["trunks"].items():
        global_rates[trk] = 0
        global_rate += convert_extension(rate)

    # Rate for each trunk (sum of destinations rates)
    for dst in data["destinations"]:
        global_rates[dst["trunk_id"]] += convert_extension(dst["rate"])

    qdisc_file.write("DEV=" + interface + "\n")
    qdisc_file.write("tc qdisc del dev $DEV root\n")
    qdisc_file.write("tc qdisc add dev $DEV root handle 1:0 cbq bandwidth 100Mbit avpkt 1000 cell 8\n")
    qdisc_file.write("tc class add dev $DEV parent 1:0 classid 1:1 cbq rate " + str(global_rate) + "bit weight " + to_kilo(global_rate//10) + "bit prio 8 allot 1514 cell 8 avpkt 1000 bounded\n\n")

    # Trunk filter
    count_trk = 0
    for trk,trk_rate in data["trunks"].items():
        count_trk = int(trk)
        rate = convert_extension(trk_rate)
        qdisc_file.write("tc class add dev $DEV parent 1:1 classid 1:" + str(10*count_trk) + " cbq rate " + str(rate) + "bit weight " + to_kilo(rate//10) + "bit prio 8 allot 1514 cell 8 avpkt 1000 bounded\n")

        for dst in data["destinations"]:
            if dst["trunk_id"] == trk:
                address = dst["destination_address"]
                qdisc_file.write("tc filter add dev $DEV protocol ip parent 1:0 prio " + str(count_trk) + " u32 match ip dst " + address + "/32 flowid 1:" + str(10*count_trk) + "\n")
        qdisc_file.write("\n")

        qdisc_file.write("tc qdisc add dev $DEV parent 1:" + str(10*count_trk) + " handle " + str(10*count_trk) + ":0 cbq bandwidth 100Mbit avpkt 1000 cell 8\n")
        qdisc_file.write("tc class add dev $DEV parent " + str(10*count_trk) + ":0 classid " + str(10*count_trk) + ":1 cbq rate " + str(global_rates[trk]) + "bit weight " + to_kilo(global_rates[trk]//10) + "bit prio 8 allot 1514 cell 8 avpkt 1000 bounded\n\n")

        # Destination filter
        count_dst = 0
        for dst in data["destinations"]:
            if dst["trunk_id"] != trk:
                continue
            count_dst += 1
            rate = convert_extension(dst["rate"])
            address = dst["destination_address"]
            qdisc_file.write("tc class add dev $DEV parent " + str(10*count_trk) + ":1 classid " + str(10*count_trk) + ":" + str(10*count_dst) + " cbq rate " + str(rate) + "bit weight " + to_kilo(rate//10) + "bit prio 8 allot 1514 cell 8 avpkt 1000 bounded\n")
            qdisc_file.write("tc filter add dev $DEV protocol ip parent " + str(10*count_trk) + ":0 prio " + str(count_dst) + " u32 match ip dst " + address + "/32 flowid " + str(10*count_trk) + ":" + str(10*count_dst) + "\n")

            # CoS filter
            id_prio = str(count_dst) + str(count_trk) + "0"
            if dst["qos"]:
                qdisc_file.write("tc qdisc add dev $DEV parent " + str(10*count_trk) + ":" + str(10*count_dst) + " handle " + id_prio + ": prio bands 4 priomap 0 0 1 1 2 2 3 3 3 0 0 0 0 0 0 0\n")

                for prio in range(4):
                    term_data = dst["qos"]["prio_"+str(prio)]
                    AQM = term_data["AQM"]
                    rate = convert_extension(term_data["rate"])
                    limit = term_data["limit"]
                    qdisc_file.write("tc qdisc add dev $DEV parent " + id_prio + ":" + str(prio+1) + " handle " + id_prio + str(prio+1) + ": tbf rate " + str(rate) + "bit burst 32kbit limit " + str(limit) + "\n")
                    if AQM:
                        AQMs.append("tc qdisc add dev $DEV parent " + id_prio + str(prio+1) + ": " + AQM + "\n")
            else:
                limit = dst["limit"]

                qdisc_file.write("tc qdisc add dev $DEV parent " + str(10*count_trk) + ":" + str(10*count_dst) + " handle " + id_prio + "9: tbf rate " + str(rate) + "bit burst 32kbit limit " + str(limit) + "\n")
            
            qdisc_file.write("\n")
        qdisc_file.write("\n")

    for cmd in AQMs:
        qdisc_file.write(cmd)

    qdisc_file.write("\ntc -s qdisc ls dev $DEV")

    qdisc_file.close()


def add_scheduler(interface,file):
    json_file = open(file,"r")
    data = json.load(json_file, object_pairs_hook=OrderedDict)
    json_file.close()
    create_commands(data,interface)

    cmd = ['bash', '/tmp/qdisc_generated.sh']
    run_command(cmd)


def remove_scheduler(interface):
    cmd = ['tc', 'qdisc', 'del', 'dev', interface, 'root']
    run_command(cmd)


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/ip_scheduler/ip_scheduler_rstats_filter.conf'):
    
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
        parser.add_argument('interface', type=str, help='Interface to apply or delete scheduler')
    
        subparsers = parser.add_subparsers(title='Subcommand mode', help='Choose between adding or removing scheduler')
        subparsers.required=True
    
        parser_remove = subparsers.add_parser('remove', help='Remove all rules')
        parser_add    = subparsers.add_parser('add', help='Add a new scheduler')
    
        parser_add.add_argument('file', type=str, help='Path (on the agent) to the configuration file describing the scheduler')
    
        parser_remove.set_defaults(function=remove_scheduler)
        parser_add.set_defaults(function=add_scheduler)
    
        args = vars(parser.parse_args())
        main = args.pop('function')
        main(**args)
