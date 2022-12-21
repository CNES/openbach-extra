#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016-2023 CNES
#
#
#   This file is part of the OpenBACH testbed.
#
#
#   OpenBACH is a free software : you can redistribute it and/or modify it under
#   the terms of the GNU General Public License as published by the Free Software
#   Foundation, either version 3 of the License, or (at your option) any later
#   version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
#   details.
#
#   You should have received a copy of the GNU General Public License along with
#   this program. If not, see http://www.gnu.org/licenses/.

""" Helpers of ftp_srv and ftp_clt jobs """


def ftp_single(
        scenario, client_entity, server_entity, server_ip, port, mode,
        file_path, ftp_user=None, ftp_password=None, blocksize=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    """File transfer (upload or download) between FTP server and client.

    Create the server, then the client. The client uploads or downloads
    a single file, then the server stops.

    The path file needs to consider /srv/ as root or home directory.
    """
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'ftp_srv', server_entity,
            server_ip=server_ip,
            port=port, user=ftp_user,
            password=ftp_password)

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=1)
    client.configure(
            'ftp_clt', client_entity,
            server_ip=server_ip,
            port=port, user=ftp_user,
            password=ftp_password,
            blocksize=blocksize,
            mode=mode,
            own={
                'file_path': file_path,
            })

    stopper = scenario.add_function('stop_job_instance', wait_finished=[client])
    stopper.configure(server)

    return [server]

def ftp_multiple(
        scenario, client_entity, server_entity, server_ip, port, mode,
        file_path, multiple, ftp_user=None, ftp_password=None, blocksize=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    """Multiple file transfer (upload or download) between FTP server and client.

    Create the server, then the client. The client uploads or downlaods
    a single file multiple times, then the server stops.

    The path file needs to consider /srv/ as root or home directory.
    """
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'ftp_srv', server_entity,
            server_ip=server_ip,
            port=port, user=ftp_user,
            password=ftp_password)

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=1)
    client.configure(
            'ftp_clt', client_entity,
            server_ip=server_ip,
            port=port, user=ftp_user,
            password=ftp_password,
            blocksize=blocksize,
            mode=mode,
            own={
                'file_path': file_path,
            })

    for n in range(1, multiple):
        client = scenario.add_function(
                'start_job_instance',
                wait_finished=[client])
        client.configure(
                'ftp_clt', client_entity,
                server_ip=server_ip,
                port=port, user=ftp_user,
                password=ftp_password,
                blocksize=blocksize,
                mode=mode,
                own={
                    'file_path': file_path,
                })

    stopper = scenario.add_function('stop_job_instance', wait_finished=[client])
    stopper.configure(server)

    return [server]


def ftp_server(
        scenario, server_entity, server_ip, port,
        ftp_user=None, ftp_password=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'ftp_srv', server_entity,
            server_ip=server_ip,
            port=port, user=ftp_user,
            password=ftp_password)
    return [server]


def ftp_client(
        scenario, client_entity, server_ip, port, mode,
        file_path, ftp_user=None, ftp_password=None, blocksize=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    client = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    client.configure(
            'ftp_clt', client_entity,
            server_ip=server_ip,
            port=port, user=ftp_user,
            password=ftp_password,
            blocksize=blocksize,
            mode=mode,
            own={
                'file_path': file_path,
            })
    return [client]
