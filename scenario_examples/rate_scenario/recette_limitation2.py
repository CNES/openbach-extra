#!/usr/bin/env python3

import itertools
import argparse
import json
import ipaddress
import os
import re

import matplotlib.pyplot as plt
from scenario_observer import ScenarioObserver

import scenario_builder as sb


SCENARIO_NAME = 'Metrology FAIRNESS TRANSPORT'
SCENARIO_DESCRIPTION = 'This scenario aims at comparing the fairness and performance of two congestion controls for different SATCOM system characteristics.'

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
        client1_entity, client2_entity, servera_entity, serverb_entity, gw_entity, st_entity,
        owd_server_gw=(10,), cc=('cc', )): 
    # Create the scenario with scenario_builder
    scenario = sb.Scenario('QoS_metrics', 'This scenario analyse the path between server and client in terms of maximum date rate (b/s) and one-way delay (s)')
    scenario.add_argument('dst_ip_serverA', 'ServerA IP') 
    scenario.add_argument('dst_ip_serverB', 'ServerB IP') 
    scenario.add_argument('port', 'The port of the nuttcp/iperf3 server ')
    scenario.add_constant('com_port', '6000') #The port of nuttcp server for signalling
    scenario.add_constant('duration', '10') # The duration of each test (sec.)
    scenario.add_constant('udp_rate', '30M') # The port of nuttcp server for signalling
    scenario.add_argument('iface_servera', 'iface of serverA')
    scenario.add_argument('iface_serverb', 'iface of serverB')
    scenario.add_argument('iface_gw', 'iface of GW to LAN')
    configurations = itertools.product(
               cc, owd_server_gw)
    wait_finished=[]
    jobs_to_postprocess = []

    for cc, owd in configurations:
        if cc == 'bb':
            cca='bbr'
            ccb='bbr'
        if cc == 'cc':
            cca = 'cubic'
            ccb = 'cubic'
        else:
            cca = 'cubic'
            ccb = 'bbr'
        
        # Configure OWD of links 
        conf_link_servera_gw = scenario.add_function(
               'start_job_instance',
               wait_finished=wait_finished
        )
        conf_link_servera_gw.configure(
               'configure_link', servera_entity,
               interface_name='$iface_servera', delay=owd,
        )
        conf_link_serverb_gw = scenario.add_function(
               'start_job_instance',
               wait_finished=wait_finished
        )
        conf_link_serverb_gw.configure(
               'configure_link', serverb_entity,
               interface_name='$iface_serverb', delay=owd,
        )     
        conf_link_gw_servers = scenario.add_function(
               'start_job_instance',
               wait_finished=wait_finished
        )
        conf_link_gw_servers.configure(
               'configure_link', gw_entity,
               interface_name='$iface_gw', delay=owd,
        )
        launch_sysctl = scenario.add_function(
               'start_job_instance',
               wait_finished=wait_finished
        )
        launch_sysctl.configure('sysctl', servera_entity,
                parameter='net.ipv4.tcp_available_congestion_control', value=cca,
        )
        launch_sysctl = scenario.add_function(
               'start_job_instance',
               wait_finished=wait_finished
        )
        launch_sysctl.configure('sysctl', serverb_entity,
                parameter='net.ipv4.tcp_available_congestion_control', value=ccb,
        ) 
        # Analyse rate with nuttcp 
        launch_nuttcpserver = scenario.add_function(
                'start_job_instance',
                wait_finished=[launch_sysctl, conf_link_servera_gw, conf_link_serverb_gw, conf_link_gw_servers],
                wait_delay=2,
        )
        launch_nuttcpserver.configure(
                'nuttcp', servera_entity, offset=0,
                command_port='$com_port', server={},
        )
        launch_nuttcpclient = scenario.add_function(
                'start_job_instance',
                wait_launched=[launch_nuttcpserver],
                wait_delay=2,
        )
        launch_nuttcpclient.configure(
                'nuttcp', client1_entity, offset=0,
                command_port='$com_port', client = {'server_ip':'$dst_ip_serverA',
               'port':'$port', 'receiver':'{0}'.format(False), 
               'duration':'$duration', 'rate_limit':'$udp_rate', 'udp':{}}
        )
        stop_nuttcpserver = scenario.add_function(
               'stop_job_instance',
                wait_finished=[launch_nuttcpclient],
        )
        stop_nuttcpserver.configure(launch_nuttcpserver)
    
        # Analyse OWD with owamp-server/client
        owamp_servera = scenario.add_function('start_job_instance',
                wait_launched = [stop_nuttcpserver]
        )
        owamp_servera.configure('owamp-server', servera_entity, offset=0,
                server_address='$dst_ip_serverA')
    
        owamp_client1 = scenario.add_function('start_job_instance',
                wait_launched=[owamp_servera],
                wait_delay=5)
        owamp_client1.configure('owamp-client', client1_entity, offset=0,
                destination_address='$dst_ip_serverA')
    
        stop_pings = scenario.add_function('stop_job_instance',
                wait_finished=[owamp_client1])
        
        stop_pings.configure(owamp_servera)

        # Performance test with iperf3 from serverA to client1 
        launch_iperf3serverA = scenario.add_function(
               'start_job_instance',
               wait_finished=[owamp_servera],
               wait_delay=2,
        )
        launch_iperf3serverA.configure(
               'iperf3', servera_entity, offset=0, port='$port',
               server = {'exit':True},
        )
        launch_iperf3client1 = scenario.add_function(
               'start_job_instance',
               wait_launched=[launch_iperf3serverA],
               wait_delay=2,
        )
        launch_iperf3client1.configure(
               'iperf3', client1_entity, offset=0,
               port='$port', client = {'server_ip':'$dst_ip_serverA',
               'transmitted_size':'100M', 'tcp':{}}
        )
        # Performance test with iperf3 from server B to client2
        launch_iperf3serverB = scenario.add_function(
               'start_job_instance',
               wait_finished=[owamp_servera],
               wait_delay=2,
        )
        launch_iperf3serverB.configure(
               'iperf3', serverb_entity, offset=0, port='$port',
               server = {'exit':True},
        )
        launch_iperf3client2 = scenario.add_function(
               'start_job_instance',
               wait_launched=[launch_iperf3serverB],
               wait_delay=2,
        )
        launch_iperf3client2.configure(
               'iperf3', client2_entity, offset=0,
               port='$port', client = {'server_ip':'$dst_ip_serverB',
               'transmitted_size':'100M', 'tcp':{}}
        )
        jobs_to_postprocess.extend((launch_nuttcpclient, owamp_client1, launch_iperf3serverA, launch_iperf3serverB))
        
        wait_finished = [launch_iperf3serverA, launch_iperf3serverB]
    
    # Post-processing
    pp_time_series = scenario.add_function(
           'start_job_instance', wait_finished=wait_finished, wait_delay=2
    )
    pp_time_series.configure(
           'time_series', client1_entity, offset=0,
           jobs=jobs_to_postprocess, statistics=[['rate'], ['owd_sent'], ['throughput']],
           ylabels=[['transmitted_data(bits)'],['OWD(sec)'],['throughput(b/s)']], titles=[['Validation of OWD'],['Validation of rate'],['Throughput Comparison']],
    )
    pp_histo = scenario.add_function(
           'start_job_instance', wait_finished=wait_finished, wait_delay=2
    )
    pp_histo.configure(
           'histogram', client1_entity, offset=0,
           jobs=jobs_to_postprocess, bins=100, statistics=[['sent_data']],
           ylabels=['transmitted_data(bits)'], titles=['CDF of transmitted data'],
           cummulative=True,
    )
     
    return scenario


def build_main_scenario(
     client1_entity, client2_entity, servera_entity, serverb_entity, gw_entity, st_entity, project_name,
    configure_opensand, opensand_emulation):
	
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_DESCRIPTION)

    # Create subscenarios QoS_metrics and File_transfer
    metrics_sce = build_metrics_scenario(client1_entity, client2_entity, servera_entity, serverb_entity, gw_entity, st_entity)
    observer1 = ScenarioObserver(metrics_sce.name, project_name, metrics_sce)
    
    # Launch subscenarios OpenSAND (conf and emu) and QoS_metrics 
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
    metrics_sub = scenario.add_function(
              'start_scenario_instance',
              wait_launched=[opensand_emu],
              wait_delay=10,
    )
    metrics_sub.configure(
              metrics_sce.name,
              dst_ip_serverA='192.168.42.5',
              dst_ip_serverB='192.168.42.3',
              port=7000,
              iface_servera='ens8',
              iface_serverb='ens8',
              iface_gw='ens9',
    )
    return scenario

def main(project_name, configure_opensand, opensand_emulation):
    #Build a scenario specifying the entity name of the client and the server.
    scenario_builder = build_main_scenario('client', 'client2', 'serverA', 'serverB', 'GW', 'ST', project_name, configure_opensand, opensand_emulation )
    observer = ScenarioObserver(SCENARIO_NAME, project_name, scenario_builder)
    observer.launch_and_wait()


if __name__ == '__main__':

    # Build scenario to configure/reset OpenSAND hosts
    configure_opensand, reset_opensand = build_scenario_opensand_hosts(json_file('/home/exploit/openbach-extra/scenario_examples/rate_scenario/topology.json'))

    # Build scenario to run OpenSAND emulation
    opensand_emulation = build_scenario_opensand_emulation(json_file('/home/exploit/openbach-extra/scenario_examples/rate_scenario/topology.json'))
    main('rate_jobs', configure_opensand, opensand_emulation) 
