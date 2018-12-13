#!/usr/bin/env python3

import argparse
import json
import ipaddress
import os
import re
import itertools

import matplotlib.pyplot as plt
from scenario_observer import ScenarioObserver

import scenario_builder as sb


SCENARIO_NAME = 'Metrology FAIRNESS TRANSPORT'
SCENARIO_DESCRIPTION = 'This scenario aims at comparing the fairness and performance of two congestion controls for different SATCOM system characteristics.'
NUTTCP_CLIENT_UDP_LABEL = 'nuttcp client: {} flows, rate {}, mtu {}b, tos {} (iter {})'
NUTTCP_SERVER_UDP_LABEL = 'nuttcp server: {} flows, rate {}, mtu {}b, tos {} (iter {})'
CLIENT_TCP_LABEL = '{} client: {} flows, mtu {}, tos {} (iter {})'
SERVER_TCP_LABEL = '{} server: {} flows, mtu {}, tos {} (iter {})'
POST_PROC = []

# OpenSAND conf
NETWORKS='networks'
HOSTS='hosts'
NAME='name'
IPV4='ipv4'
IPV6='ipv6'
ADDRESS='address'
NETDIGIT='netdigit'
IFACES='ifaces'
NETWORK='network'
TYPE='opensand-entity'
ID='opensand-entity-id'
SAT='sat'
ST='st'
GW='gw'
MANAGEMENT='management'
EMULATION='emulation'
LAN='^lan.*$'
OPENSAND_TUN='opensand_tun'
OPENSAND_RUN='opensand_run'
PLATFORM='platform'

def find_items_with_param(items, param, val):
    '''
    Find the list of dictionary containing a parameter with an expected value in a list.
    Args:
        items:  list of dictionary in which find item
        param:  parameter to check value
        val:    expected parameter value
    Returns:
        the list of dictionary containing a parameter with the expected value.
    Raises:
        KeyError:  if one item has not the parameter
    '''
    return [item for item in items if param in item and item[param] == val]
    
def find_one_item_with_param(items, param, val):
    '''
    Find the only one dictionary containing a parameter with an expected value in a list.
    Args:
        items:  list of dictionary in which find item
        param:  parameter to check value
        val:    expected parameter value
    Returns:
        the dictionary containing a parameter with the expected value.
    Raises:
        KeyError:    if one item has not the parameter
        ValueError:  if no item or more than one found
    '''
    sub_items = find_items_with_param(items, param, val)
    if len(sub_items) != 1:
        raise ValueError('No or more than one items found')
    return sub_items[0]

def find_one_item_with_regex(items, param, regex):
    '''
    Find the only one dictionary containing a parameter that matches with a regex in a list.
    Args:
        items:  list of dictionary in which find item
        param:  parameter to check value
        regex:  regex to match
    Returns:
        the dictionary containing a parameter that matches the regex.
    Raises:
        ValueError:  if no item or more than one found
    '''
    matches = [item for item in items if param in item and re.match(regex, item[param])]
    if len(matches) != 1:
        raise ValueError('No or more than one items found')
    return matches[0]

    
def build_scenario_opensand_hosts(topology):
    '''
    Build scenario to configure and reset OpenSAND hosts.
    Args:
        topology:  description of the topology
    Returns:
        conf_scen:      scenario to configure OpenSAND hosts
        reset_scen:  scenario to reset the OpenSAND hosts configuration
    Raises:
        ValueError:  if topology has not valid values
    '''
    conf_scen = sb.Scenario('*** BUILT *** Configure OpenSAND platform', '')
    reset_scen = sb.Scenario('*** BUILT *** Reset OpenSAND platform', '')
    platform = topology[PLATFORM]
    lans = {}

    # Get OpenSAND network settings
    try:
        network = find_one_item_with_param(topology[NETWORKS], NAME, MANAGEMENT)
        mng_net4_digit = network[IPV4][NETDIGIT]
    except (KeyError, ValueError):
        raise ValueError('Invalid {} network settings format'.format(MANAGEMENT))
    try:
        network = find_one_item_with_param(topology[NETWORKS], NAME, EMULATION)
        emu_net4_digit = network[IPV4][NETDIGIT]
    except (KeyError, ValueError):
        raise ValueError('Invalid {} network settings format'.format(EMULATION))
            
    # Get OpenSAND satellites settings
    try:
        sats = find_items_with_param(topology[HOSTS], TYPE, SAT)
        for sat in sats:
            sat_name = sat[NAME]
 #           sat_id = sat[ID]
            iface = find_one_item_with_param(sat[IFACES], NETWORK, MANAGEMENT)
            mng_iface = iface[NAME]
            iface = find_one_item_with_param(sat[IFACES], NETWORK, EMULATION)
            emu_iface = iface[NAME]
            emu_ipv4 = '{}/{}'.format(iface[IPV4], emu_net4_digit)
            func = conf_scen.add_function('start_job_instance')
            func.configure(
                'opensand_conf', sat_name, offset=0,
                **{
                    'entity-type': SAT,
#                    'entity-id': sat_id, 
                    'ctrl-iface': mng_iface,
                    'emu-iface': emu_iface,
                    'emu-ipv4' : emu_ipv4,
                    'platform-id':platform,
                }
            )
            func = reset_scen.add_function('start_job_instance')
            func.configure(
                'opensand_conf', sat_name, offset=0,
                **{
                    'entity-type': 'none',
                    'ctrl-iface': mng_iface,
                    'emu-iface': emu_iface,
                    'emu-ipv4' : emu_ipv4,
                }
            )
    except (KeyError, ValueError):
        raise ValueError('Invalid {} host format'.format(SAT))

    # Get OpenSAND gateways settings
    try:
        gws = find_items_with_param(topology[HOSTS], TYPE, GW)
        for gw in gws:
            gw_name = gw[NAME]
            gw_id = gw[ID]
            iface = find_one_item_with_param(gw[IFACES], NETWORK, MANAGEMENT)
            mng_iface = iface[NAME]
            iface = find_one_item_with_param(gw[IFACES], NETWORK, EMULATION)
            emu_iface = iface[NAME]
            emu_ipv4 = '{}/{}'.format(iface[IPV4], emu_net4_digit)
            iface = find_one_item_with_regex(gw[IFACES], NETWORK, LAN)
            lan_iface = iface[NAME]
            lan_name = iface[NETWORK]
            try:
                network = find_one_item_with_param(topology[NETWORKS], NAME, lan_name)
                lan_net4_digit = network[IPV4][NETDIGIT]
                lan_net6_digit = network[IPV6][NETDIGIT]
            except (KeyError, ValueError):
                raise ValueError('Invalid {} network settings format'.format(lan_name))
            lan_ipv4 = '{}/{}'.format(iface[IPV4], lan_net4_digit)
            lan_ipv6 = '{}/{}'.format(iface[IPV6], lan_net6_digit)
            func = conf_scen.add_function('start_job_instance')
            func.configure(
                'opensand_conf', gw_name, offset=0,
                **{
                    'entity-type': GW,
                    'ctrl-iface': mng_iface,
                    'emu-iface': emu_iface,
                    'emu-ipv4': emu_ipv4,
                    'platform-id': platform,
                    'entity-id': gw_id,
                    'lan-iface': lan_iface,
                    'lan-ipv4': lan_ipv4,
                    'lan-ipv6': lan_ipv6,
                }
            )
            func = reset_scen.add_function('start_job_instance')
            func.configure(
                'opensand_conf', gw_name, offset=0,
                **{
                    'entity-type': 'none',
                    'ctrl-iface': mng_iface,
                    'emu-iface': emu_iface,
                    'emu-ipv4' : emu_ipv4,
                }
            )
            lans[lan_name] = iface[IPV4]
    except (KeyError, ValueError):
        raise ValueError('Invalid {} host format'.format(GW))

    # Get OpenSAND terminals settings
    try:
        sts = find_items_with_param(topology[HOSTS], TYPE, ST)
        for st in sts:
            st_name = st[NAME]
            st_id = st[ID]
            iface = find_one_item_with_param(st[IFACES], NETWORK, MANAGEMENT)
            mng_iface = iface[NAME]
            iface = find_one_item_with_param(st[IFACES], NETWORK, EMULATION)
            emu_iface = iface[NAME]
            emu_ipv4 = '{}/{}'.format(iface[IPV4], emu_net4_digit)
            iface = find_one_item_with_regex(st[IFACES], NETWORK, LAN)
            lan_iface = iface[NAME]
            lan_name = iface[NETWORK]
            try:
                network = find_one_item_with_param(topology[NETWORKS], NAME, lan_name)
                lan_net4_digit = network[IPV4][NETDIGIT]
                lan_net6_digit = network[IPV6][NETDIGIT]
            except (KeyError, ValueError):
                raise ValueError('Invalid {} network settings format'.format(lan_name))
            lan_ipv4 = '{}/{}'.format(iface[IPV4], lan_net4_digit)
            lan_ipv6 = '{}/{}'.format(iface[IPV6], lan_net6_digit) 
            func = conf_scen.add_function('start_job_instance')
            func.configure(
                'opensand_conf', st_name, offset=0,
                **{
                    'entity-type': ST,
                    'ctrl-iface': mng_iface,
                    'emu-iface': emu_iface,
                    'emu-ipv4': emu_ipv4,
                    'platform-id': platform,
                    'entity-id': st_id,
                    'lan-iface': lan_iface,
                    'lan-ipv4': lan_ipv4,
                    'lan-ipv6': lan_ipv6,
                }
            )
            func = reset_scen.add_function('start_job_instance')
            func.configure(
                'opensand_conf', st_name, offset=0,
                **{
                    'entity-type': 'none',
                    'ctrl-iface': mng_iface,
                    'emu-iface': emu_iface,
                    'emu-ipv4' : emu_ipv4,
                }
            )
            lans[lan_name] = iface[IPV4]
    except (KeyError, ValueError):
            raise ValueError('Invalid {} host format'.format(ST))

    # Get OpenSAND work stations settings
    try:
        for ws in topology[HOSTS]:
            if TYPE in ws:
                continue
            # Find lan
            ws_name = ws[NAME]
            iface = ws[IFACES][0]
            if iface[NETWORK] not in lans:
                continue
            lan_gw = lans[iface[NETWORK]]
            last = None
            for name in lans:
                if name == iface[NETWORK]:
                    continue
                destination = ipaddress.ip_network(
                    '{}/{}'.format(network[IPV4][ADDRESS], network[IPV4][NETDIGIT])
                )
                network = find_one_item_with_param(topology[NETWORKS], NAME, name)
                func = conf_scen.add_function('start_job_instance')
                func.configure(
                    'ip_route', ws_name, offset=0,
                    destination_ip=network[IPV4][ADDRESS],
                    subnet_mask=destination.netmask.exploded,
                    gateway_ip=lan_gw,
                    action=1,
                )
                func = reset_scen.add_function('start_job_instance')
                func.configure(
                    'ip_route', ws_name, offset=0,
                    destination_ip=network[IPV4][ADDRESS],
                    subnet_mask=destination.netmask.exploded,
                    gateway_ip=lan_gw,
                    action=0,
                )
    except (KeyError, ValueError):
            raise ValueError('Invalid {} host format'.format(ST))
    return conf_scen, reset_scen
      

def build_scenario_opensand_emulation(topology):
    '''
    Build scenario to run OpenSAN emulation.
    Args:
        topology:  description of the topology
    Returns:
        scen:  scenario to run OpenSAND emulation
    Raises:
        ValueError:  if topology has not valid values
    '''
    scen = sb.Scenario('*** BUILT *** Run OpenSAND Emulation', '')
    platform = topology[PLATFORM]
    opensand_run = topology[OPENSAND_RUN]
    scen.add_argument(
        'opensand_scenario',
        'The path of the OpenSAND scenario',
    )
    # Add function to scenarios
    func = scen.add_function(
        'start_job_instance',
    )
    func.configure(
        'opensand_run', opensand_run, offset=0,
        **{
            'platform-id': platform,
            'scenario-path': '$opensand_scenario',
        }
    )
    return scen
          
    
def json_file(value):
    '''
    Define JSON file type.
    Load JSON from file.
    Args:
        value:  JSON file path
    Returns:
        Dictionary load from JSON file
    Raises:
        ArgumentTypeError:  if file does not exist
                            if file is not readable
                            if file is not JSON
    '''
    res, fp = None, None

    try:
        fp = open(value, 'r')
    except IOError:
        raise argparse.ArgumentTypeError('Unable to read file')
    try:
        res = json.load(fp)
    except ValueError:
        raise argparse.ArgumentTypeError('Unable to load JSON')
    try:
        res[NETWORKS]
        res[HOSTS]
    except KeyError:
        raise argparse.ArgumentTypeError('Invalid JSON format')
    finally:
        if fp != None:
            fp.close()
    return res
 


def build_metrics_scenario(
        client_entity, server_entity):
    
    # Create the scenario with scenario_builder
    scenario = sb.Scenario('QoS_metrics', 'This scenario analyse the path between server and client in terms of maximum date rate (b/s) and one-way delay (s)')
    scenario.add_argument('dst_ip', '192.168.19.3') # The IP of the server
    scenario.add_argument('port', '7000') # The port of the server
    scenario.add_constant('com_port', '6000') # The port of nuttcp server for signalling
    scenario.add_constant('duration', '10') # The duration of each test (sec.)

    # Configure/Launch nuttcp 

    launch_nuttcpserver = scenario.add_function(
            'start_job_instance'
    )
    launch_nuttcpserver.configure(
            'nuttcp', server_entity, offset=0,
            command_port='$com_port', server={}
    )
    launch_nuttcpclient = scenario.add_function(
            'start_job_instance',
            wait_launched=[launch_nuttcpserver],
            wait_delay=2,
    )
    launch_nuttcpclient.configure(
            'nuttcp', client_entity, offset=0,
            command_port='$com_port', client = {'server_ip':'$dst_ip',
           'port':'$port', 'receiver':'{0}'.format(False), 
           'duration':'$duration', 'rate_limit':'{0}'.format('10M'), 'udp':{}}
    )
    stop_nuttcpserver = scenario.add_function(
           'stop_job_instance',
            wait_finished=[launch_nuttcpclient],
    )
    stop_nuttcpserver.configure(launch_nuttcpserver)

    # Job 'owamp-server'
    owamp_server = scenario.add_function('start_job_instance',
            wait_launched = [stop_nuttcpserver])

    owamp_server.configure('owamp-server', server_entity, offset=0,
            server_address='$dst_ip')

    # Job 'owamp-client'
    owamp_client = scenario.add_function('start_job_instance',
            wait_launched=[owamp_server],
            wait_delay=5)
    owamp_client.configure('owamp-client', client_entity, offset=0,
            destination_address='$dst_ip')

    stop_pings = scenario.add_function('stop_job_instance',
            wait_finished=[owamp_client])
    
    stop_pings.configure(owamp_server)

    return scenario

def build_rate_scenario(
           client_entity, server_entity):
   
    scenario = sb.Scenario('File_transfer', 'This scenarios modifies the TCP congestion control of a server and transmits a 100MB file between an iperf3 server and an iperf3 client')
    scenario.add_argument('dst_ip', 'The IP of the iperf3 server') # The IP of the server
    scenario.add_argument('port', 'The port of the iperf3 server') # The port of the server
    scenario.add_argument('cc_servera', 'Congestion Control of server A')
    scenario.add_argument('iface_servera', 'One-way delay from server to GW')
    scenario.add_argument('delay_server_gw', 'One-way delay from server to GW')

    #scenario.add_argument('cc_serverb', 'Congestion Control of server B')


    conf_link_server_gw = scenario.add_function(
           'start_job_instance',
    )
    conf_link_server_gw.configure(
           'configure_link', server_entity,
           interface_name='$iface_servera', delay="$delay_server_gw",
    )
    
    launch_sysctl = scenario.add_function(
           'start_job_instance',
    )
    launch_sysctl.configure('sysctl', server_entity,
            parameter='net.ipv4.tcp_available_congestion_control', value='$cc_servera',
    )
    
    #launch_sysctlserverb.configure(
    #      'sysctl', server_entity,
    #       parameter='net.ipv4.tcp_available_congestion_control', value='cc_serverb',
    #)

    launch_iperf3server = scenario.add_function(
           'start_job_instance',
           label='iperf3_server',
           wait_finished=[launch_sysctl],
           wait_delay=2,
    )
    launch_iperf3server.configure(
           'iperf3', server_entity, offset=0, port='$port',
           server = {'exit':True},
    )
    launch_iperf3client = scenario.add_function(
           'start_job_instance',
           wait_launched=[launch_iperf3server, conf_link_server_gw],
           wait_delay=2,
    )
    launch_iperf3client.configure(
           'iperf3', client_entity, offset=0,
           port='$port', client = {'server_ip':'$dst_ip',
           'transmitted_size':'100M', 'tcp':{}}
    )
    wait_finished = [launch_iperf3client, launch_iperf3server]

    return scenario


def build_main_scenario(
    client_entity, server_entity, project_name,
    configure_opensand, opensand_emulation,
    owd_server_gw=(1,), cca=('cubic',)):
	
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_DESCRIPTION)

	# Create subscenarios QoS_metrics and File_transfer
    metrics_sce = build_metrics_scenario(client_entity, server_entity)
    metrics_sce.write('metrics.json')
    observer1 = ScenarioObserver(metrics_sce.name, project_name, metrics_sce)
    rate_sce = build_rate_scenario(client_entity, server_entity)
    observer2 = ScenarioObserver(rate_sce.name, project_name, rate_sce)
    rate_sce.write('rate.json')
	
	# Launch subscenarios QoS_metrics and File_transfer
    configurations = itertools.product(
	       cca, owd_server_gw)
    wait_finished=[]
    conf_opensand = scenario.add_function(
              'start_scenario_instance',
    )
    conf_opensand.configure(
              configure_opensand.name,
    )
 
    opensand_emu = scenario.add_function(
              'start_scenario_instance',
               wait_finished=[conf_opensand],
               wait_delay=10,
    )
    opensand_emu.configure(
              opensand_emulation.name,
              opensand_scenario='/home/exploit/.opensand/recette_openbach',
    )
    wait_finished=[]
    wait_launched=[opensand_emu]
    for cc, owd in configurations:
	
        metrics_sub = scenario.add_function(
                  'start_scenario_instance',
                  wait_finished=wait_finished,
                  wait_launched=wait_launched,
                  wait_delay=10,
	)
        wait_launched=[]
        metrics_sub.configure(
                  metrics_sce.name,
                  dst_ip='192.168.19.3',
                  port=7000,
        )
        rate_sub = scenario.add_function(
                  'start_scenario_instance',
                   wait_finished=[metrics_sub],
                   wait_delay=2,
        )
        rate_sub.configure(
                   rate_sce.name,
                   dst_ip='192.168.19.3',
                   port=7000,
                   cc_servera=cc,
                   #cc_serverb='cubic',
                   iface_servera='ens8',
                   delay_server_gw=owd, 
        )
        wait_finished = [rate_sub]
    return scenario

def main(project_name, configure_opensand, opensand_emulation):
    #Build a scenario specifying the entity name of the client and the server.
    scenario_builder = build_main_scenario('client', 'client2', project_name, configure_opensand, opensand_emulation )
    #scenario_builder.write('your_scenario.json')
    
    observer = ScenarioObserver(SCENARIO_NAME, project_name, scenario_builder)
    observer.launch_and_wait()


if __name__ == '__main__':

    # Build scenario to configure/reset OpenSAND hosts
    configure_opensand, reset_opensand = build_scenario_opensand_hosts(json_file('/home/exploit/openbach-extra/scenario_examples/rate_scenario/topology.json'))
    #configure_opensand.write(os.path.join(args.output,'configure_opensand.json'))
    #reset_opensand.write(os.path.join(args.output, 'reset_opensand.json'))

    # Build scenario to run OpenSAND emulation
    opensand_emulation = build_scenario_opensand_emulation(json_file('/home/exploit/openbach-extra/scenario_examples/rate_scenario/topology.json'))
    #opensand_emulation.write(os.path.join(args.output, 'opensand_emulation.json')) 
    main('rate_jobs', configure_opensand, opensand_emulation)
