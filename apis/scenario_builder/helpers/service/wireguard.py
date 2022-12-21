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

""" Helpers of openvpn job """
from nacl.public import PrivateKey
from base64 import b64encode, b64decode
from ..utils import filter_none

SERVER_TUN_IP = "10.10.10.1/24"
CLIENT_TUN_IP = "10.10.10.2/24"
ALLOWED_IPS = "0.0.0.0/0"
PORT = 8888

# From https://github.com/fictivekin/wireguard/blob/master/wireguard/utils/keys.py


def generate_key():
    """Generates a new private key"""
    private = PrivateKey.generate()
    return b64encode(bytes(private)).decode("ascii")


def public_key(private_key):
    """Given a private key, returns the corresponding public key"""
    private = PrivateKey(b64decode(private_key))
    return b64encode(bytes(private.public_key)).decode("ascii")


def wireguard_create_interface(scenario, entity, tun_ip, private_key, tun_dev="tun0", listen_port=0, mtu=None,
                               wait_finished=None, wait_launched=None, wait_delay=0):

    create_interface = scenario.add_function(
        'start_job_instance',
        wait_finished=wait_finished,
        wait_launched=wait_launched,
        wait_delay=wait_delay
    )

    creation_params = filter_none(
        tun_ip=tun_ip,
        private_key=private_key,
        listen_port=listen_port,
        mtu=mtu
    )

    create_interface.configure(
        "wireguard", entity, offset=0, tun_dev=tun_dev, create_interface=creation_params
    )

    return [create_interface]


def wireguard_set_peer(scenario, entity, peer_pub_key, tun_dev="tun0", allowed_ips=None, endpoint=None, persistent_keepalive=None,
                       wait_finished=None, wait_launched=None, wait_delay=0):

    add_peer = scenario.add_function(
        'start_job_instance',
        wait_finished=wait_finished,
        wait_launched=wait_launched,
        wait_delay=wait_delay
    )

    peer_params = filter_none(
        peer_pub_key=peer_pub_key,
        allowed_ips=allowed_ips,
        endpoint=endpoint,
        persistent_keepalive=persistent_keepalive
    )

    add_peer.configure(
        "wireguard", entity, offset=0, tun_dev=tun_dev, peer=peer_params
    )

    return [add_peer]


def wireguard_create_interface_and_set_peer(scenario, entity, tun_ip, private_key, peer_pub_key, tun_dev="tun0", listen_port=0,
                                            allowed_ips=None, endpoint=None, mtu=None, persistent_keepalive=None,
                                            wait_finished=None, wait_launched=None, wait_delay=0):
    """
    Create an interface and set peer.
    Return a couple (wait_finished, wait_launched)

    """
    create_interface = wireguard_create_interface(scenario, entity, tun_ip, private_key, tun_dev=tun_dev, listen_port=listen_port, mtu=mtu,
                                                  wait_finished=wait_finished, wait_launched=wait_launched, wait_delay=wait_delay)

    add_peer = wireguard_set_peer(scenario, entity, peer_pub_key, tun_dev=tun_dev, allowed_ips=allowed_ips, endpoint=endpoint, persistent_keepalive=persistent_keepalive,
                                  wait_launched=create_interface, wait_delay=2)

    return add_peer, create_interface


def wireguard(
        scenario, server_entity, client_entity, server_ip, client_ip=None,
        server_listen_port=PORT, client_listen_port=None,
        server_tun_dev="tun0", client_tun_dev="tun0",
        server_tun_ip=SERVER_TUN_IP, client_tun_ip=CLIENT_TUN_IP,
        server_key=generate_key(), client_key=generate_key(),
        server_allowed_ips=ALLOWED_IPS, client_allowed_ips=ALLOWED_IPS,
        mtu=None, server_persistent_keepalive=None, client_persistent_keepalive=None,
        wait_finished=None, wait_launched=None, wait_delay=0):
    """
    Create two interfaces and set peers.
    Return a couple (wait_finished, wait_launched)

    """

    client_endpoint = server_ip+":"+str(server_listen_port)
    server_endpoint = None

    if client_ip is not None:
        if client_listen_port is None:
            client_listen_port = PORT
        server_endpoint = client_ip+":"+str(client_listen_port)

    launch_server = wireguard_create_interface_and_set_peer(
        scenario, server_entity, server_tun_ip, server_key, public_key(client_key), tun_dev=server_tun_dev,
        listen_port=server_listen_port, allowed_ips=server_allowed_ips, mtu=mtu, persistent_keepalive=server_persistent_keepalive, endpoint=server_endpoint,
        wait_finished=wait_finished, wait_launched=wait_launched, wait_delay=wait_delay)

    launch_client = wireguard_create_interface_and_set_peer(
        scenario, client_entity, client_tun_ip, client_key, public_key(server_key), tun_dev=client_tun_dev,
        listen_port=client_listen_port, allowed_ips=client_allowed_ips, endpoint=client_endpoint, mtu=mtu, persistent_keepalive=client_persistent_keepalive,
        wait_finished=wait_finished, wait_launched=wait_launched, wait_delay=wait_delay)

    return launch_server[0] + launch_client[0], launch_server[1] + launch_client[1]
