#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2020 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

"""This scenario builds and launches the OpenSAND scenario
from /openbach-extra/apis/scenario_builder/scenarios/
"""


import tempfile
import argparse 
import collections
import ipaddress

from auditorium_scripts.scenario_observer import ScenarioObserver
from auditorium_scripts.push_file import PushFile
from scenario_builder.scenarios import opensand


class network_member:
    def __init__(self, entity, interface, ip, route_ip, route_gw_ip):
        self.entity = entity
        self.interface = interface
        self.ip = ip
        self.route_ip = route_ip
        self.route_gw_ip = route_gw_ip


class ST(network_member):
    def __init__(self, entity, interface, ip, opensand_ip, route_ip, route_gw_ip):
       super(ST, self).__init__(entity, interface, ip, route_ip, route_gw_ip)
       self.opensand_ip = opensand_ip


class GW(ST):
    def __init__(self, entity, interface, ip, opensand_ip, route_ip, route_gw_ip, st_list, host_list,
            gw_phy_entity = None, gw_phy_interface = None, gw_phy_ip = None):
        super(GW, self).__init__(entity, interface, ip, opensand_ip, route_ip, route_gw_ip)
        self.gw_phy_entity = None
        if gw_phy_entity is not None:
            self.gw_phy_entity = gw_phy_entity
            self.gw_phy_ip = gw_phy_ip
            self.gw_phy_interface = gw_phy_interface
        self.st_list = st_list
        self.host_list = host_list


def set_route_ip(ip):
    return str(ipaddress.ip_interface(ip).network) 


def get_route_ip_list(ip_list, ip):
    for n in range(0, len(ip_list)):
        if ip.split('.')[2] == ip_list[n].split('.')[2]:
           return ip_list[:n] + ip_list[(n+1):]
    return []
        

def validate_ip(ip):
    try:
        return str(ipaddress.ip_interface(ip))
    except ValueError:
        print('address/netmask is invalid:', ip)
        exit()


class validate_gateway(argparse.Action):
    def __call__(self, parser, args, values, option_string = None): 
        if getattr(args, self.dest) == None:
            self.items = []
        gw_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip = values
        lan_ip = validate_ip(lan_ip)
        emu_ip = validate_ip(emu_ip)
        opensand_ip = validate_ip(opensand_ip)
        Gateway = collections.namedtuple('Gateway', 'gw_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip')
        self.items.append(Gateway(gw_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip))
        setattr(args, self.dest, self.items)


class validate_gateway_phy(argparse.Action):
    def __call__(self, parser, args, values, option_string = None):
        if getattr(args, self.dest) == None:
            self.items = []
        gw_phy_entity, lan_interface, emu_interface, lan_ip, emu_ip, gw_entity = values
        lan_ip = validate_ip(lan_ip)
        emu_ip = validate_ip(emu_ip)
        Gateway_phy = collections.namedtuple('Gateway_phy', 'gw_phy_entity, lan_interface, emu_interface, lan_ip, emu_ip, gw_entity')
        self.items.append(Gateway_phy(gw_phy_entity, lan_interface, emu_interface, lan_ip, emu_ip, gw_entity))
        setattr(args, self.dest, self.items)


class validate_satellite_terminal(argparse.Action):
    def __call__(self, parser, args, values, option_string = None):
        if getattr(args, self.dest) == None:
            self.items = []
        st_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip, gw_entity = values
        lan_ip = validate_ip(lan_ip)
        emu_ip = validate_ip(emu_ip)
        opensand_ip = validate_ip(opensand_ip)
        Satellite_terminal = collections.namedtuple('Satellite_terminal', 'st_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip, gw_entity')
        self.items.append(Satellite_terminal(st_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip, gw_entity))
        setattr(args, self.dest, self.items)


class validate_client(argparse.Action):
    def __call__(self, parser, args, values, option_string = None):
        if getattr(args, self.dest) == None:
            self.items = []
        client_entity, interface, ip, st_entity = values
        ip = validate_ip(ip)
        Client = collections.namedtuple('Client', 'clt_entity, interface, ip, st_entity')
        self.items.append(Client(client_entity, interface, ip, st_entity))
        setattr(args, self.dest, self.items)


class validate_server(argparse.Action):
    def __call__(self, parser, args, values, option_string = None):
        if getattr(args, self.dest) == None:
            self.items = []
        server_entity, interface, ip, gw_entity = values
        ip = validate_ip(ip)
        Server = collections.namedtuple('Server', 'srv_entity, interface, ip, gw_entity')
        self.items.append(Server(server_entity, interface, ip, gw_entity))
        setattr(args, self.dest, self.items)


def set_gateways(sat_entity, sat_interface, sat_ip, gateway, satellite_terminal, client, server, gateway_phy = []):
    # Set hosts' route ip
    host_route_ip = str(ipaddress.ip_interface(str(ipaddress.ip_interface(sat_ip).ip) + '/16').network)
    gateways = []
    for gw in gateway:
       gw_srv = None
       gw_clt = []
       gw_st = []
       route_ip = [set_route_ip(gw.lan_ip)]
       st_route_gw_ip = str(ipaddress.ip_interface(gw.opensand_ip).ip)
       st_opensand_ip = []
       gw_phy_entity = None
       gw_phy_interface = []
       gw_phy_ip = []
       st_list = []
       gw_phy_entity = None
       gw_phy_interface = []
       gw_phy_ip = []
       
       #Set server
       for srv in server:
           if srv.gw_entity == gw.gw_entity:
               gw_srv = network_member(srv.srv_entity, srv.interface, srv.ip, host_route_ip, str(ipaddress.ip_interface(gw.lan_ip).ip))
               break
       if gw_srv == None:
           raise ValueError('Gateway must have a server')

       #Set gateway phy
       if gateway_phy is not None:
           for gwp in gateway_phy:
               if gwp.gw_entity == gw.gw_entity:
                  gw_phy_entity = gwp.gw_phy_entity
                  gw_phy_interface = [gwp.lan_interface, gwp.emu_interface]
                  gw_phy_ip = [gwp.lan_ip, gwp.emu_ip]
                  break

       #Set server route_ip
       for st in satellite_terminal:
           if st.gw_entity == gw.gw_entity:
               route_ip.append(set_route_ip(st.lan_ip))
               st_list.append(st)
               st_opensand_ip.append(str(ipaddress.ip_interface(st.opensand_ip).ip))
       if len(st_list) == 0:
           raise ValueError('Gateway must have at least one satellite terminal')

       #Set satellite terminal list
       for st in st_list:
          gw_st.append(
             ST(st.st_entity, [st.lan_interface, st.emu_interface], [st.lan_ip, st.emu_ip], st.opensand_ip, 
                get_route_ip_list(route_ip, st.lan_ip), st_route_gw_ip))

          #Set client list
          for clt in client:
              if clt.st_entity == st.st_entity:
                  gw_clt.append(network_member(clt.clt_entity, clt.interface, clt.ip, host_route_ip, str(ipaddress.ip_interface(st.lan_ip).ip)))
                  break
       if len(gw_st) != len(gw_clt):
           raise ValueError('Each satellite terminal must have only one client')

       gateways.append(GW(
                         gw.gw_entity, [gw.lan_interface, gw.emu_interface], [gw.lan_ip, gw.emu_ip], gw.opensand_ip,
                         get_route_ip_list(route_ip, gw.lan_ip), st_opensand_ip, gw_st, gw_clt + [gw_srv], 
                         gw_phy_entity, gw_phy_interface, gw_phy_ip))
    return gateways   


def main(scenario_name='opensand', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--sat', '-s', required=True, nargs=3, type=str,
            metavar=('SAT_ENTITY', 'SAT_INTERFACE', 'SAT_IP'),
            help='Info for the satellite : sat_entity, sat_interface and sat_ip')
    observer.add_scenario_argument(
            '--gateway', '-gw', required=True, action=validate_gateway, nargs=6, type=str,
            help='Info for GW: gw_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip',
            metavar=('GW_ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP','EMU_IP', 'OPENSAND_IP'))
    observer.add_scenario_argument(
            '--gateway_phy', '-gwp', required=False, action=validate_gateway_phy, nargs=6, type=str,
            help='Info for GW_PHY: gw_phy_entity, lan_interface, emu_interface, lan_ip, emu_ip, gw_entity',
            metavar=('GW_PHY_ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP','EMU_IP', 'GW_ENTITY'))
    observer.add_scenario_argument(
            '--satellite_terminal', '-st', required=True, action=validate_satellite_terminal, nargs=7, type=str,
            help='Info for ST: st_entity, lan_interface, emu_interface, lan_ip, emu_ip, opensand_ip, gw_entity', 
            metavar=('ST_ENTITY', 'LAN_INTERFACE', 'EMU_INTERFACE', 'LAN_IP', 'EMU_IP', 'OPENSAND_IP', 'GW_ENTITY'))
    observer.add_scenario_argument(
            '--client', '-clt', required=True, action=validate_client, nargs=4, type=str,
            help='Info for CLT: clt_entity, interface, interface, lan_ip, st_entity',
            metavar=('CLIENT_ENTITY', 'INTERFACE', 'IP', 'ST_ENTITY'))
    observer.add_scenario_argument(
            '--server', '-srv', required=True, action=validate_server, nargs=4, type=str,
            help='Info for SRV: srv_entity, interface, interface, lan_ip, gw_entity',
            metavar=('SERVER_ENTITY', 'INTERFACE', 'IP', 'GW_ENTITY'))

    args = observer.parse(argv, scenario_name)

        
    gateways = set_gateways(
      sat_entity=args.sat[0],
      sat_interface=args.sat[1],
      sat_ip=args.sat[2],
      gateway=args.gateway,
      gateway_phy=args.gateway_phy,
      satellite_terminal=args.satellite_terminal,
      client=args.client,
      server=args.server)
    
   
    scenario = opensand.build(gateways, args.sat[0], args.sat[1], args.sat[2])
    observer.launch_and_wait(scenario)

    #old opensand
    """
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', '-e', required=True,
            help='Entity of the agent to send files to')
    observer.add_scenario_argument(
            '--transfert', required=True,
            type=argparse.FileType('r'),
            help='File to transfert as /opt/openbach/agent/bite.txt')
    observer.add_scenario_argument(
            '--content', '-c', default='Empty file',
            help='Alternative content for /opt/openbach/agent/toto.txt')

    args = observer.parse(argv, scenario_name)
    print(args)

    pusher = observer._share_state(PushFile)
    pusher.args.keep = True

    pusher.args.local_file = args.transfert
    pusher.args.remote_path = '/opt/openbach/agent/bite.txt'
    pusher.execute(True)

    with tempfile.NamedTemporaryFile('w+') as f:
        print(args.content, file=f, flush=True)
        f.seek(0)

        pusher.args.local_file = f
        pusher.args.remote_path = '/opt/openbach/agent/toto.txt'
        pusher.execute(True)

    scenario = opensand.build(args.entity)
    observer.launch_and_wait(scenario)
    """

if __name__ == '__main__':
    main()
