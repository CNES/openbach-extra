#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   OpenBACH is a generic testbed able to control/configure multiple
   network/physical entities (under test) and collect data from them. It is
   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
   Agents (one for each network entity that wants to be tested).
   
   
   Copyright © 2016 CNES
   
   
   This file is part of the OpenBACH testbed.
   
   
   OpenBACH is a free software : you can redistribute it and/or modify it under the
   terms of the GNU General Public License as published by the Free Software
   Foundation, either version 3 of the License, or (at your option) any later
   version.
   
   This program is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
   details.
   
   You should have received a copy of the GNU General Public License along with
   this program. If not, see http://www.gnu.org/licenses/.
   
   
   
   @file     opensand_conf.py
   @brief    Sources of the Job opensand-conf
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
   @author   Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
   @author   Aurelien DELRIEU <adelrieu@toulouse.viveris.com>
"""

import os
import sys
import syslog
import argparse
import ipaddress
import netifaces
import tempfile
import subprocess

sys.path.append('/usr/lib/python3/dist-packages/')
import collect_agent


class OpsError(Exception):
    ''' OpenSAND error '''

    def __init__(self, message):
        '''
        Initialize openSAND error.
        '''
        collect_agent.send_log(syslog.LOG_ERR, message)
        super(OpsError, self).__init__(self, message)


class OpsEntity(object):
    ''' OpenSAND Entity '''

    def __init__(self, entity_type, platform_id):
        '''
        Initialize entity with arguments.
        
        Args:
            entity_type:   the type of the entity.
            platform_id:   the platform identifier (can be None).
        '''
        self._debconf_params = {}

        self._debconf_params['opensand-daemon/service/name_adv'] = entity_type

        self._debconf_params['opensand-daemon/service/type'] = \
                self._get_ops_service_type(platform_id)

        self._debconf_params['opensand-daemon/output/libpath'] = \
                '/usr/lib/libopensand_output_openbach.so.0'

    def _get_ops_service_type(self, platform_id):
        '''
        Get the OpenSAND service type.
        
        Args:
            platform_id:  the string identifying the OpenSAND platform.

        Returns:
            the OpenSAND service type.
        '''
        if platform_id is None or platform_id == '':
            return '_opensand._tcp'
        return '_{}_opensand._tcp'.format(platform_id)

    def __configure(self):
        '''
        Set the debconf configuration for OpenSAND daemon.
        
        Raises:
            OpsError:  if setting the debconf configuration failed.
        '''
        # Create a temporary script to set the Debconf
        with tempfile.NamedTemporaryFile('w+', delete=False) as fp:
            fp.write('#!/bin/sh -e\n')
            fp.write('. /usr/share/debconf/confmodule\n')
            for (key, value) in self._debconf_params.items():
                fp.write('db_set {} {}\n'.format(key, value))

        # Set file executable
        try:
            os.chmod(fp.name, 755)
        except OSError:
            raise OpsError('Configuration failed: unable to set file executable')

        # Launch the debconf settings script
        proc = subprocess.run(['bash', fp.name])
        if proc.returncode != 0:
            raise OpsError('Configuration failed: unable to set debconf')
        
        # Remove temporary file
        os.remove(fp.name)

    def __stop_daemon(self):
        '''
        Stop the OpenSAND daemon.
        '''
        subprocess.run(['systemctl', 'stop', 'opensand-daemon'])

    def __start_daemon(self):
        '''
        Start the OpenSAND daemon.
        
        Raises:
            OpsError:  if the OpenSAND daemon failed.
        '''
        proc = subprocess.run(['systemctl', 'restart', 'opensand-daemon'])
        if proc.returncode != 0:
            raise OpsError('Starting the OpenSAND Daemon failed')

    def run(self):
        '''
        Configure the OpenSAND daemon as the expected entity
        '''
        self.__stop_daemon()
        self.__configure()
        self.__start_daemon()


class EmuOpsEntity(OpsEntity):
    def __init__(self,
                 entity_type,
                 platform_id,
                 ctrl_iface,
                 emu_iface,
                 emu_ipv4,
                 service_port,
                 command_port,
                 state_port
                ):
        '''
        Initialize satellite emulator with arguments.

        Args:
            entity_type:   the type of the entity.
            platform_id:   the platform identifier (can be None)
            ctrl_iface:    the control interface of the OpenSAND daemon.
            emu_iface:     the interface to emulate the satellite network.
            emu_ipv4:      the IPv4 address to assign to the emulation
                           interface.
            service_port:  the port to listen control request.
            command_port:  the port to listen command.
            state_port:    the port to listen state request.
        '''
        super(EmuOpsEntity, self).__init__(entity_type, platform_id)
        
        self._debconf_params['opensand-daemon/service/interface'] = ctrl_iface

        self._debconf_params['opensand-daemon/network/emu_iface'] = emu_iface
        self._debconf_params['opensand-daemon/network/emu_ipv4'] = emu_ipv4

        self._debconf_params['opensand-daemon/service/port'] = service_port
        self._debconf_params['opensand-daemon/command/port'] = command_port
        self._debconf_params['opensand-daemon/state/port'] = state_port

class LanEmuOpsEntity(EmuOpsEntity):

    def __init__(self,
                 entity_type,
                 platform_id,
                 ctrl_iface,
                 emu_iface,
                 emu_ipv4,
                 service_port,
                 command_port,
                 state_port,
                 entity_id,
                 lan_iface,
                 lan_ipv4,
                 lan_ipv6
                ):
        '''
        Initialize gateway with arguments.

        Args:
            entity_type:   the type of the entity.
            platform_id:   the platform identifier (can be None)
            ctrl_iface:    the control interface of the OpenSAND daemon.
            emu_iface:     the interface to emulate the satellite network.
            emu_ipv4:      the IPv4 address to assign to the emulation
                           interface.
            service_port:  the port to listen control request.
            command_port:  the port to listen command.
            state_port:    the port to listen state request.
            entity_id:     the identifier of the gateway. 
            lan_iface:     the interface to connect to the real network.
            lan_ipv4:      the IPv4 address to assign to the lan interface.
            lan_ipv6:      the IPv6 address to assign to the lan interface.
        '''
        super(LanEmuOpsEntity, self).__init__(
            entity_type,
            platform_id,
            ctrl_iface,
            emu_iface,
            emu_ipv4,
            service_port,
            command_port,
            state_port
        )

        self._debconf_params['opensand-daemon/service/st_instance'] = entity_id

        self._debconf_params['opensand-daemon/network/lan_iface'] = lan_iface
        self._debconf_params['opensand-daemon/network/lan_ipv4'] = lan_ipv4
        self._debconf_params['opensand-daemon/network/lan_ipv6'] = lan_ipv6

def ops_iface(value):
    '''
    Define OpenSAND interface.
    Check value is matching or not.
    
    Args:
        value:  the value to check.
    
    Returns:
        the matching value.

    Raises:
        ArgumentTypeError:  if value is not matching the OpenSAND format for
                            interface.
    '''
    #Parse local ifaces, without lo, opensand_tun, opensand_tap
    reserved_ifaces = ['lo', 'opensand_tun', 'opensand_tap']
    ifaces = filter(lambda x: x not in reserved_ifaces, netifaces.interfaces())
    if value not in ifaces:
        raise argparse.ArgumentTypeError('Invalid interface ({})'.format(', '.join(ifaces)))

    return value

def ops_ipv4(value):
    '''
    Define OpenSAND IPv4 format to X.X.X.X/Y.
    Check value is matching or not.
    
    Args:
        value:  the value to check.
    
    Returns:
        the matching value.

    Raises:
        ArgumentTypeError:  if value is not matching the OpenSAND format for
                            IPv4 address.
    '''
    max_prefixlen = 28  # 32 - 2^2
    #dummy = ipaddress.IPv4Network(value.decode('utf-8'), strict=False)
    dummy = ipaddress.IPv4Network(value, strict=False)
    if max_prefixlen < dummy.prefixlen:
        raise argparse.ArgumentTypeError('Invalid prefix length (<={})'.format(max_prefixlen))
    return value

def ops_ipv6(value):
    '''
    Define OpenSAND IPv6 format to X::X/Y.
    Check value is matching or not.
    
    Args:
        value:  the value to check.
    
    Returns:
        the matching value.

    Raises:
        ArgumentTypeError:  if value is not matching the OpenSAND format for
                            IPv6 address.
    '''
    max_prefixlen = 124  # 128 - 2^2
    #dummy = ipaddress.IPv6Network(value.decode('utf-8'), strict=False)
    dummy = ipaddress.IPv6Network(value, strict=False)
    if max_prefixlen < dummy.prefixlen:
        raise argparse.ArgumentTypeError('Invalid prefix length (<={})'.format(max_prefixlen))
    return value

def ops_st_id(value):
    '''
    Define OpenSAND satellite terminal identifier.
    Check value is matching or not.
    
    Args:
        value:  the value to check.
    
    Returns:
        the matching value.

    Raises:
        ArgumentTypeError:  if value is not matching the OpenSAND format for
                            satellite terminal identifier.
    '''
    id = int(value)

    if id not in list(range(1, 6)) + list(range(7, 11)):
        raise argparse.ArgumentTypeError('Invalid ST id (1-5 or 7-10)')

    return id

def ops_gw_id(value):
    '''
    Define OpenSAND gateway identifier.
    Check value is matching or not.
    
    Args:
        value:  the value to check.
    
    Returns:
        the matching value.

    Raises:
        ArgumentTypeError:  if value is not matching the OpenSAND format for
                            gateway identifier.
    '''
    id = int(value)

    if id not in [0, 6]:
        raise argparse.ArgumentTypeError('Invalid GW id (0 or 6)')

    return id
   
def ops_port(value):
    '''
    Define OpenSAND port.
    Check value is matching or not.
    
    Args:
        value:  the value to check.
    
    Returns:
        the matching value.

    Raises:
        ArgumentTypeError:  if value is not matching the OpenSAND format for
                            port.
    '''
    try:
        port = int(value)
    except TypeError:
        raise argparse.ArgumentTypeError('Invalid port (1-65535)')

    if port <= 0 or 65535 < port:
        raise argparse.ArgumentTypeError('Invalid port (1-65535)')
    
    return port

if __name__ == '__main__':
    # Define Usage
    parser = argparse.ArgumentParser(description='Configure an OpenSAND entity',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Entity sub command
    entity_cmd = parser.add_subparsers(dest='entity_type',
                                       metavar='entity_type',
                                       help='The type of the entity')
    entity_cmd.required = True
    none_parser = entity_cmd.add_parser('none', help='Disable entity')
    sat_parser = entity_cmd.add_parser('sat', help='Satellite emulator')
    st_parser = entity_cmd.add_parser('st', help='Satellite terminal')
    gw_parser = entity_cmd.add_parser('gw', help='Gateway')
   
    st_parser.add_argument('--entity-id', type=ops_st_id, required=True,
                           help='The entity id '
                           '(1-5 or 7-10)')
    gw_parser.add_argument('--entity-id', type=ops_gw_id, required=True,
                           help='The entity id '
                           '(0 or 6)')

    all_parsers = (none_parser, sat_parser, st_parser, gw_parser)
    emu_parsers = (sat_parser, st_parser, gw_parser)
    lan_parsers = (st_parser, gw_parser)

    for all_parser in all_parsers:
        # Entity optional arguments
        all_parser.add_argument('--platform-id', type=str,
                                help='The plateform id (default is none)')

    for emu_parser in emu_parsers:
        # Emulation entity required arguments
        emu_parser.add_argument('ctrl_iface', type=ops_iface,
                                help='The interface used to control the OpenSAND Daemon')
        emu_parser.add_argument('emu_iface', type=ops_iface,
                                help='The interface used to emulate the satellite network')
        emu_parser.add_argument('emu_ipv4', type=ops_ipv4,
                                help='The IPv4 address to set to the "emu-iface"'
                                'interface (format X.X.X.X/X)')

        # Emulation entity optional arguments
        emu_parser.add_argument('--service-port', type=ops_port, default=3141,
                                help='The port to receive information about other entitites '
                                '(default: 3141)')
        emu_parser.add_argument('--command-port', type=ops_port, default=5926,
                                help='The port to receive command from the manager '
                                '(default: 5926)')
        emu_parser.add_argument('--state-port', type=ops_port, default=5358,
                                help='The port to receive status requestes from the manager '
                                '(default: 5358)')

    for lan_parser in lan_parsers:
        # Lan and emulation entity required arguments
        lan_parser.add_argument('--lan-iface', type=ops_iface, required=True,
                                help='The interface used to receive/send traffic')
        lan_parser.add_argument('--lan-ipv4', type=ops_ipv4, required=True,
                                help='The IPv4 address to set to the "lan-iface" interface '
                                '(format X.X.X.X/X)')
        lan_parser.add_argument('--lan-ipv6', type=ops_ipv6, required=True,
                                help='The IPv6 address to set to the "lan-iface" interface '
                                'format X::X/X')

    # Get args
    args = parser.parse_args()

    # Prepare constructors in function of the entity type
    constructors = {
        'none': OpsEntity,
        'sat': EmuOpsEntity,
        'st': LanEmuOpsEntity,
        'gw': LanEmuOpsEntity
    }
    
    # Connect to collect agent
    collect_agent.register_collect(
            '/opt/openbach/agent/jobs/opensand_conf/opensand_conf_rstats_filter.conf')
    collect_agent.send_log(syslog.LOG_DEBUG, "Starting job opensand_conf")

    # Create and run the entity
    entity = constructors[args.entity_type](**vars(args))
    entity.run()
