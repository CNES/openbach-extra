#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
# Author:  / <@toulouse.viveris.com>

import collect_agent
from controller_GW_MM import ControllerProxyMM
from controller_GW import ControllerProxy

if __name__ == '__main__':
    def proxy_type(arg):
        return { arg.split(':')[0] : ':'.join(arg.split(':')[1:]) }

    def comma_separated_list(arg):
        return set(map(str.strip, arg.split(',')))

    parser = argparse.ArgumentParser(
            description='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            '-m', '--mm', action='store_true', help='Use MM')
    parser.add_argument(
            'norm_tx_iface', type=str, help='Norm Tx interface')
    parser.add_argument(
            'server_ip', type=str, help='The IP address of the server')
    parser.add_argument(
            'content_dir', type=str, help='The directory of the content')
    parser.add_argument(
            'squid_cache_dir', type=str, help='The Squid cache directory')
    parser.add_argument(
            'formatted_files_dir', type=str, help='The dir to store formatted files')
    parser.add_argument(
            'multicast_contents', type=str, help='Path of the file containing the contents')
    parser.add_argument(
            'quality', type=str, choices=['max', 'min', 'average'],
            help='The quality of the content to use')
    parser.add_argument(
            'resolutions', type=comma_separated_list,
            help='The available of the content')
    parser.add_argument(
            'content_name', type=str,
            help='The name of the content')
    parser.add_argument(
            'content_name_short', type=str,
            help='The short name of the content')
    parser.add_argument(
            'segment_duration', type=int,
            help='The duration of each video segment')
    parser.add_argument(
            'proxy_url', type=proxy_type,
            help='The proxy url')
    parser.add_argument(
            'mpd_date', type=str,
            help='The date on the name of the mpd file')
    parser.add_argument(
            '--multicast-a-address', type=str,
            default='224.1.2.3', help='Multicast A address')
    parser.add_argument(
            '--multicast-a-port', type=int,
            default=6143, help='Multicast A port')
    parser.add_argument(
            '--multicast-b-address', type=str,
            default='224.1.2.4', help='Multicast B address')
    parser.add_argument(
            '--multicast-b-port', type=int,
            default=6142, help='Multicast B port')
    parser.add_argument(
            '--norm-maxrate', type=int,
            default=17000000, help='Multicast B port')
    parser.add_argument(
            '--resolution', type=int, default=4219897,
            help='The resolution of the content')


    args = parser.parse_args()

    conffile = '/opt/openbach/agent/jobs/twinkle_voip/mbr_manager_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    if args.mm:
        controller = ControllerProxyMM(
                args.resolution, args.content_dir, args.multicast_contents,
                args.content_name, args.content_name_short, args.mpd_date,
                args.segment_duration, args.multicast_a_address, args.multicast_a_port,
                args.multicast_b_address, args.multicast_b_port, args.norm_maxrate,
                args.norm_tx_iface, args.proxy_url, args.server_ip, args.squid_cache_dir,
                args.formatted_files_dir)
    else:
        controller = ControllerProxy(
                args.norm_tx_iface, args.server_ip, args.content_dir,
                args.squid_cache_dir, args.formatted_files_dir,
                args.multicast_contents, args.quality, args.resolutions,
                args.content_name, args.content_name_short, args.segment_duration,
                args.multicast_a_address, args.multicast_a_port,
                args.multicast_b_address, args.multicast_b_port,
                args.norm_maxrate, args.proxy_url, args.mpd_date)

    controller.start()

    def stop_wrapper(sig_number, stack_frame):
        controller.stop()

    signal.signal(signal.SIGINT, stop_wrapper)
    signal.signal(signal.SIGTERM, stop_wrapper)

    try:
        controller.wait()
    except KeyboardInterrupt:
        controller.stop()
