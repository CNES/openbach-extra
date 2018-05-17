#!/usr/bin/env python3

import os
import re
import sys

def cache(squid_cache_dir, formatted_files_dir, server_ip,
        segment_duration, content_name, content_name_short):

    mpd_file_pattern = re.compile(
            r'http://{}/vod-dash/{}/{}sec/(.+[.]mpd)'.format(
                server_ip, content_name, segment_duration))
    mp4_file_pattern = re.compile(
            r'http://{}/vod-dash/{}/{}sec/{}_([0-9]+)bps/(.+[.]mp4)'.format(
                server_ip, content_name, segment_duration, content_name_short))
    m4s_file_pattern = re.compile(
            r'http://{}/vod-dash/{}/{}sec/{}_([0-9]+)bps/(.+[.]m4s)'.format(
                server_ip, content_name, segment_duration, content_name_short))

    for root, dirs, files in os.walk(squid_cache_dir, topdown=True):
        for cache_filename in files:
            found = False
            with open(os.path.join(root,
                                   cache_filename),"rb") as openfile:
                num_end_header = 0
                for num, line in enumerate(openfile, 1):
                    if m4s_file_pattern.search(line.decode('latin1')):
                        file_type = "m4s"
                        m4s_groups = m4s_file_pattern.search(line.decode('latin1'))
                        resolution = m4s_groups.group(1)
                        filename = m4s_groups.group(2)
                        found = True
                    elif mp4_file_pattern.search(line.decode('latin1')):
                        file_type = "mp4"
                        mp4_groups = mp4_file_pattern.search(line.decode('latin1'))
                        resolution = mp4_groups.group(1)
                        filename = mp4_groups.group(2)
                        found = True
                    elif mpd_file_pattern.search(line.decode('latin1')):
                        file_type = "mpd"
                        mpd_groups = mpd_file_pattern.search(line.decode('latin1'))
                        filename = mpd_groups.group(1)
                        found = True
                    if line == b'\r\n':
                        num_end_header = num
                        
                        break

            if not found:
                continue

            with open(os.path.join(root, cache_filename), "rb") as f:
                data = f.readlines()
            data_size = os.stat(os.path.join(root, cache_filename)).st_size
            
            for k in data[0:num_end_header]:
                data_size -= len(k)
            del data[0:num_end_header]

            storing_directory = formatted_files_dir if file_type == "mpd" else \
                    '{0}{1}_{2}bps/'.format(
                            formatted_files_dir, content_name_short, resolution)
            filepath = os.path.join(storing_directory, filename)

            try:
                file_size = os.stat(filepath).st_size
            except OSError:
                file_size = 0

            if file_size == 0:
                with open(filepath, 'wb') as fout:
                    fout.writelines(data)

