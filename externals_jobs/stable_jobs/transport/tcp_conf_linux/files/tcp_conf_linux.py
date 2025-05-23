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


"""Sources of the Job tcp_conf_linux"""


__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Bastien TAURAN <bastien.tauran@viveris.com>
 * Francklin SIMO <francklin.simo@viveris.com>
'''

import sys
import syslog
import argparse
import subprocess
from pathlib import Path

import collect_agent


def run_command(command, debug_log, exit=False):
    try:
        subprocess.run(command)
        collect_agent.send_log(syslog.LOG_DEBUG, debug_log)
    except Exception as ex:
        message = '{}:{}'.format(command, ex)
        collect_agent.send_log(syslog.LOG_WARNING, message)
        if exit:
           sys.exit(message)


def check_cc(congestion_control_name):
    out = subprocess.run(
            ['sysctl', 'net.ipv4.tcp_allowed_congestion_control'],
            check=True, stdout=subprocess.PIPE, text=True).stdout
    allowed_ccs = out.split('=')[1].rstrip().split()
    if congestion_control_name not in allowed_ccs:
        message = (
                'Specified congestion control \'{}\' is not allowed. May '
                'be its kernel module is not loaded or not installed.\n'
                'You can choose one from this list: {}.'.format(congestion_control_name, allowed_ccs)
        )
        collect_agent.send_log(syslog.LOG_ERR, message)
        sys.exit(message)


def read_from_file(filepath):
    with open(filepath) as f:
        return f.readline().strip()


def write_to_file(filepath, value):
    with open(filepath, 'w') as f:
        f.write(value)


def write_from_file_if_missing(dest, value, *net_param, base_dir='/proc/sys'):
    if value is None:
        with Path(base_dir, *net_param).open() as f:
            dest.write('.'.join(net_param) + '=' + f.readline())
    else:
        print('.'.join(net_param), value, file=dest, sep='=')


def set_main_args(reset,
        tcp_congestion_control,
        tcp_slow_start_after_idle,
        tcp_no_metrics_save,
        tcp_sack,
        tcp_recovery,
        tcp_wmem_min,
        tcp_wmem_default,
        tcp_wmem_max,
        tcp_rmem_min,
        tcp_rmem_default,
        tcp_rmem_max,
        tcp_fastopen,
        core_wmem_default,
        core_wmem_max,
        core_rmem_default,
        core_rmem_max):

    # reset to defaults config if asked
    if reset:
        # removing conf files
        command = ['rm', '-f', '/etc/sysctl.d/60-openbach-job.conf']
        debug_log = 'removing config files'
        run_command(command, debug_log)
        command = ['rm', '-f', '/etc/sysctl.d/60-openbach-job-cubic.conf']
        run_command(command, debug_log)
        # loading default config
        with open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf") as src:
            for line in src:
                name, value = line.split("=")
                while '.' in name:
                    name = name.replace('.','/')
                write_to_file('/proc/sys/' + name, value)
        with open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf") as src:
            for line in src:
                name, value = line.split("=")
                value = value.rstrip()
                write_to_file('/sys/module/tcp_cubic/parameters/' + name, value)

    # writing changes in /etc/sysctl.d/60-openbach-job.conf
    with open('/etc/sysctl.d/60-openbach-job.conf', 'w') as conf_file:
        conf_file.write('# configuration file generated by the OpenBACH job tcp_conf_linux\n')
        write_from_file_if_missing(conf_file, tcp_congestion_control, 'net', 'ipv4', 'tcp_congestion_control')
        write_from_file_if_missing(conf_file, tcp_slow_start_after_idle, 'net', 'ipv4', 'tcp_slow_start_after_idle')
        write_from_file_if_missing(conf_file, tcp_no_metrics_save, 'net', 'ipv4', 'tcp_no_metrics_save')
        write_from_file_if_missing(conf_file, tcp_sack, 'net', 'ipv4', 'tcp_sack')
        write_from_file_if_missing(conf_file, tcp_recovery, 'net', 'ipv4', 'tcp_recovery')

        with open('/proc/sys/net/ipv4/tcp_wmem') as src:
            wmem_min, wmem_default, wmem_max = src.read().split()
        if tcp_wmem_min is None:
            tcp_wmem_min = wmem_min
        if tcp_wmem_default is None:
            tcp_wmem_default = wmem_default
        if tcp_wmem_max is None:
            tcp_wmem_max = wmem_max
        print('net.ipv4.tcp_wmem=', file=conf_file, end='')
        print(tcp_wmem_min, tcp_wmem_default, tcp_wmem_max, file=conf_file)

        with open('/proc/sys/net/ipv4/tcp_rmem') as src:
            rmem_min, rmem_default, rmem_max = src.read().split()
        if tcp_rmem_min is None:
            tcp_rmem_min = rmem_min
        if tcp_rmem_default is None:
            tcp_rmem_default = rmem_default
        if tcp_rmem_max is None:
            tcp_rmem_max = rmem_max
        print('net.ipv4.tcp_rmem=', file=conf_file, end='')
        print(tcp_rmem_min, tcp_rmem_default, tcp_rmem_max, file=conf_file)

        write_from_file_if_missing(conf_file, tcp_fastopen, 'net', 'ipv4', 'tcp_fastopen')
        write_from_file_if_missing(conf_file, core_wmem_default, 'net', 'core', 'wmem_default')
        write_from_file_if_missing(conf_file, core_wmem_max, 'net', 'core', 'wmem_max')
        write_from_file_if_missing(conf_file, core_rmem_default, 'net', 'core', 'rmem_default')
        write_from_file_if_missing(conf_file, core_rmem_max, 'net', 'core', 'rmem_max')

    # loading new configuration
    command = ['systemctl', 'restart', 'procps.service']
    debug_log = 'Loading new configuration'
    run_command(command, debug_log, exit=True)

    # retrieving new values
    statistics = {}
    for param in [
            'tcp_congestion_control', 'tcp_slow_start_after_idle',
            'tcp_no_metrics_save', 'tcp_sack', 'tcp_recovery', 'tcp_fastopen',
    ]:
        statistics[param] = read_from_file('/proc/sys/net/ipv4/' + param)
    for param in ['wmem_default', 'wmem_max', 'rmem_default', 'rmem_max']:
        statistics['core_' + param] = read_from_file('/proc/sys/net/core/' + param)

    statistics['tcp_wmem_min'], statistics['tcp_wmem_default'], statistics['tcp_wmem_max'] = read_from_file('/proc/sys/net/ipv4/tcp_wmem').split()
    statistics['tcp_rmem_min'], statistics['tcp_rmem_default'], statistics['tcp_rmem_max'] = read_from_file('/proc/sys/net/ipv4/tcp_rmem').split()

    collect_agent.send_stat(collect_agent.now(), **statistics)


def cubic(reset,
        tcp_slow_start_after_idle,
        tcp_no_metrics_save,
        tcp_sack,
        tcp_recovery,
        tcp_wmem_min,
        tcp_wmem_default,
        tcp_wmem_max,
        tcp_rmem_min,
        tcp_rmem_default,
        tcp_rmem_max,
        tcp_fastopen,
        core_wmem_default,
        core_wmem_max,
        core_rmem_default,
        core_rmem_max,
        beta,
        fast_convergence,
        hystart_ack_delta,
        hystart_low_window,
        tcp_friendliness,
        hystart,
        hystart_detect,
        initial_ssthresh):
    check_cc('cubic')
    set_main_args(reset,
            "cubic",
            tcp_slow_start_after_idle,
            tcp_no_metrics_save,
            tcp_sack,
            tcp_recovery,
            tcp_wmem_min,
            tcp_wmem_default,
            tcp_wmem_max,
            tcp_rmem_min,
            tcp_rmem_default,
            tcp_rmem_max,
            tcp_fastopen,
            core_wmem_default,
            core_wmem_max,
            core_rmem_default,
            core_rmem_max)

    # Get current name of "hystart_ack_delta" parameter since it can be different
    # according to the Linux kernel
    hystart_ack_delta_name = next(hystart.name for hystart in Path('/sys/module/tcp_cubic/parameters').glob('hystart_ack_delta*'))

    # getting changes to CUBIC parameters in /etc/module/tcp_cubic/parameters and
    # writing changes in /etc/sysctl.d/60-openbach-job-cubic.conf
    with open('/etc/sysctl.d/60-openbach-job-cubic.conf','w') as conf_file:
        conf_file.write('# configuration file generated by the OpenBACH job tcp_conf_linux\n')
        conf_file.write('# warning: these values are not loaded on system startup\n')
        write_from_file_if_missing(conf_file, beta, 'beta', base_dir='/sys/module/tcp_cubic/parameters')
        write_from_file_if_missing(conf_file, fast_convergence, 'fast_convergence', base_dir='/sys/module/tcp_cubic/parameters')
        write_from_file_if_missing(conf_file, hystart_ack_delta, hystart_ack_delta_name, base_dir='/sys/module/tcp_cubic/parameters')
        write_from_file_if_missing(conf_file, hystart_low_window, 'hystart_low_window', base_dir='/sys/module/tcp_cubic/parameters')
        write_from_file_if_missing(conf_file, tcp_friendliness, 'tcp_friendliness', base_dir='/sys/module/tcp_cubic/parameters')
        write_from_file_if_missing(conf_file, hystart, 'hystart', base_dir='/sys/module/tcp_cubic/parameters')
        write_from_file_if_missing(conf_file, hystart_detect, 'hystart_detect', base_dir='/sys/module/tcp_cubic/parameters')
        write_from_file_if_missing(conf_file, initial_ssthresh, 'initial_ssthresh', base_dir='/sys/module/tcp_cubic/parameters')

    statistics = {
            'beta': beta,
            'fast_convergence': fast_convergence,
            hystart_ack_delta_name: hystart_ack_delta,
            'hystart_low_window': hystart_low_window,
            'tcp_friendliness': tcp_friendliness,
            'hystart': hystart,
            'hystart_detect': hystart_detect,
            'initial_ssthresh': initial_ssthresh,
    }

    for name, value in statistics.items():
        if value is not None:
            # applying changes
            write_to_file('/sys/module/tcp_cubic/parameters/' + name, str(value))
        # retrieving new values for tcp_cubic parameters
        statistics[name] = read_from_file('/sys/module/tcp_cubic/parameters/' + name)

    collect_agent.send_stat(collect_agent.now(), **statistics)


def other_CC(reset,
        tcp_slow_start_after_idle,
        tcp_no_metrics_save,
        tcp_sack,
        tcp_recovery,
        tcp_wmem_min,
        tcp_wmem_default,
        tcp_wmem_max,
        tcp_rmem_min,
        tcp_rmem_default,
        tcp_rmem_max,
        tcp_fastopen,
        core_wmem_default,
        core_wmem_max,
        core_rmem_default,
        core_rmem_max,
        congestion_control_name):
    congestion_control_name = congestion_control_name.lower()
    check_cc(congestion_control_name)
    set_main_args(reset,
            congestion_control_name,
            tcp_slow_start_after_idle,
            tcp_no_metrics_save,
            tcp_sack,
            tcp_recovery,
            tcp_wmem_min,
            tcp_wmem_default,
            tcp_wmem_max,
            tcp_rmem_min,
            tcp_rmem_default,
            tcp_rmem_max,
            tcp_fastopen,
            core_wmem_default,
            core_wmem_max,
            core_rmem_default,
            core_rmem_max)


if __name__ == '__main__':
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/tcp_conf_linux/tcp_conf_linux_rstats_filter.conf'):
        parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
        parser.add_argument('--reset', action='store_true', help='Resets the parameters to default configuration before applying changes')
        parser.add_argument('--tcp_slow_start_after_idle', type=int)
        parser.add_argument('--tcp_no_metrics_save', type=int)
        parser.add_argument('--tcp_sack', type=int)
        parser.add_argument('--tcp_recovery', type=int)
        parser.add_argument('--tcp_wmem_min', type=int)
        parser.add_argument('--tcp_wmem_default', type=int)
        parser.add_argument('--tcp_wmem_max', type=int)
        parser.add_argument('--tcp_rmem_min', type=int)
        parser.add_argument('--tcp_rmem_default', type=int)
        parser.add_argument('--tcp_rmem_max', type=int)
        parser.add_argument('--tcp_fastopen', type=int)
        parser.add_argument('--core_wmem_default', type=int)
        parser.add_argument('--core_wmem_max', type=int)
        parser.add_argument('--core_rmem_default', type=int)
        parser.add_argument('--core_rmem_max', type=int)
    
        subparsers = parser.add_subparsers(
                title='Subcommand mode',
                help='Choose the congestion control')
        subparsers.required=True
        parser_cubic = subparsers.add_parser('CUBIC', help='CUBIC chosen')
        parser_cubic.add_argument('--beta', type=int)
        parser_cubic.add_argument('--fast_convergence', type=int)
        parser_cubic.add_argument('--hystart_ack_delta', type=int)
        parser_cubic.add_argument('--hystart_low_window', type=int)
        parser_cubic.add_argument('--tcp_friendliness', type=int)
        parser_cubic.add_argument('--hystart', type=int)
        parser_cubic.add_argument('--hystart_detect', type=int)
        parser_cubic.add_argument('--initial_ssthresh', type=int)
    
        parser_other = subparsers.add_parser('other', help='other CC chosen')
        parser_other.add_argument('congestion_control_name', type=str)
    
        parser_cubic.set_defaults(function=cubic)
        parser_other.set_defaults(function=other_CC)
    
        args = vars(parser.parse_args())
    
        main = args.pop('function')
        main(**args)
