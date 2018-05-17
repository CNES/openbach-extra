#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
# Author:  / <@toulouse.viveris.com>


import collect_agent
from controller_proxy_MM import ControllerProxyMM
from controller_proxy import ControllerProxy


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
            'rx_norm_iface', type=str, help='Norm Tx interface')
    parser.add_argument(
            'rx_norm_dir', type=str, help='Norm Tx interface')
    parser.add_argument(
            'contents_descriptor_file', type=str,
            help='Path of the file containing the contents')
    parser.add_argument(
            'segment_duration', type=int,
            help='The duration of each video segment')
    parser.add_argument(
            'mpd_dir', type=str,
            help='The directory where the mpd file is located')
    parser.add_argument(
            'proxy_url', type=proxy_type,
            help='The proxy url')
    parser.add_argument('content_name', type=str, help='The content name')
    parser.add_argument('content_name_short', type=str, help='The short content name')
    parser.add_argument('server_ip', type=str, help='The IP of the server')

    # Only needed if MM
    parser.add_argument(
            'addr_proxy_bb', type=str, help='Proxy BB address')
    parser.add_argument(
            'port_a_proxy_bb', type=int, help='Proxy BB port A')
    parser.add_argument(
            'port_b_proxy_bb', type=int, help='Proxy BB port B')

    parser.add_argument(
            '--resolutions', type=comma_separated_list,
            default={1546902, 334349, 4219897, 45652},
            help='The contents resolutions')

    args = parser.parse_args()

    conffile = '/opt/openbach/agent/jobs/twinkle_voip/mbr_client_rstats_filter.conf'
    collect_agent.register_collect(conffile)

    if args.mm:
        controller = ControllerProxyMM(
                args.addr_proxy_bb, args.port_a_proxy_bb, args.port_b_proxy_bb, args.rx_norm_dir,
                args.rx_norm_iface, args.contents_descriptor_file,
                args.mpd_dir, args.segment_duration, args.content_name,
                args.content_name_short, args.server_ip, args.proxy_url, args.resolutions)
    else:
        controller = ControllerProxy(
                args.rx_norm_iface, args.rx_norm_dir, args.contents_descriptor_file,
                args.segment_duration, args.mpd_dir, args.proxy_url, args.resolutions,
                args.content_name, args.content_name_short, args.server_ip)

    controller.start()

    def stop_wrapper(sig_number, stack_frame):
        controller.stop()

    signal.signal(signal.SIGINT, stop_wrapper)
    signal.signal(signal.SIGTERM, stop_wrapper)

    try:
        controller.wait()
    except KeyboardInterrupt:
        controller.stop()
