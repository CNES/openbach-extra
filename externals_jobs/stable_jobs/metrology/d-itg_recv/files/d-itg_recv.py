#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess


def main(log_buffer_size):

    if log_buffer_size:
        cmd = '/opt/openbach-jobs/d-itg_recv/d-itg/bin/ITGRecv -q {}'.format(log_buffer_size)
    else:
        cmd = '/opt/openbach-jobs/d-itg_recv/d-itg/bin/ITGRecv'

    subprocess.call(cmd, shell=True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create a D-ITG command',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-q', '--log_buffer_size', type=int, metavar='LOG BUFFER SIZE',
                        help='Number of packets to push to the log at once (Default: 50)')

    # get args
    args = parser.parse_args()
    log_buffer_size = args.log_buffer_size 

    main(log_buffer_size)
