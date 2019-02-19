import re
import enum
import json
import ipaddress
import itertools
from argparse import ArgumentTypeError, FileType

import scenario_builder as sb


NETWORKS = 'networks'
HOSTS = 'hosts'
NAME = 'name'
IPV4 = 'ipv4'
IPV6 = 'ipv6'
ADDRESS = 'address'
NETDIGIT = 'netdigit'
IFACES = 'ifaces'
NETWORK = 'network'
TYPE = 'opensand-entity'
ID = 'opensand-entity-id'
MANAGEMENT = 'management'
EMULATION = 'emulation'
LAN = '^lan.*$'
OPENSAND_TUN = 'opensand_tun'
OPENSAND_RUN = 'opensand_run'
PLATFORM = 'platform'


class EntityType(enum.Enum):
    SAT = 'sat'
    GW = 'gw'
    ST = 'st'


class WorkstationAction(enum.Enum):
    ADD = 1
    DELETE = 0


def find_items_with_param(items, key, value):
    """
    Find the list of dictionary containing a parameter with
    an expected value in a list.

    Args:
        items:  list of dictionary in which find item
        key:    parameter to check value
        value:  expected parameter value
    Returns:
        the list of dictionaries containing a parameter
        with the expected value.
    Raises:
        KeyError:  if one item has not the parameter
    """
    return [item for item in items if key in item and item[key] == value]


def find_item_with_param(items, key, value):
    """
    Find the only one dictionary containing a parameter with
    an expected value in a list.

    Args:
        items:  list of dictionary in which find item
        key:    parameter to check value
        value:  expected parameter value
    Returns:
        the dictionary containing a parameter with
        the expected value.
    Raises:
        KeyError:    if one item has not the parameter
        ValueError:  if no item or more than one found
    """
    item, = find_items_with_param(items, key, value)
    return item


def find_item_with_regex(items, key, regex):
    """
    Find the only one dictionary containing a parameter that
    matches with a regex in a list.

    Args:
        items:  list of dictionary in which find item
        key:    parameter to check value
        regex:  regex to match
    Returns:
        the dictionary containing a parameter that
        matches the regex.
    Raises:
        KeyError:    if one item has not the parameter
        ValueError:  if no item or more than one found
    """
    match, = [item for item in items if key in item and re.match(regex, item[key])]
    return match


def remove_items_with_param(items, key, *values):
    """
    Find the list of dictionary not containing a parameter with
    value in a list.

    Args:
        items:   list of dictionary in which remove items
        key:     parameter to check value
        values:  not expected parameter values
    Returns:
        the dictionary not containing a parameter with the expected values.
    Raises:
        KeyError:    if one item has not the parameter
    """
    return [item for item in items if key not in item or item[key] not in values]


def find_interface(entity, network_name):
    return find_item_with_param(entity[IFACES], NETWORK, network_name)


def find_host_by_name(topology, name):
    return find_item_with_param(topology[HOSTS], NAME, name)


def find_common_lan_network(*hosts):
    lans = [remove_items_with_param(host[IFACES], NETWORK, MANAGEMENT, EMULATION) for host in hosts]

    lan_names = (set(lan[NETWORK] for lan in l) for l in lans)
    names = next(lan_names, set())
    for names_ in lan_names:
        names.intersection_update(names_)

    lan_name = names.pop()
    return [find_item_with_param(host[IFACES], NETWORK, lan_name) for host in hosts]


def format_address(interface, network, protocol=IPV4):
    return '{}/{}'.format(interface[protocol], network[protocol][NETDIGIT])


def configure_entity(scenario, entity, entity_type, networks, platform_id):
    emulation_network = find_item_with_param(networks, NAME, EMULATION)

    management_interface = find_interface(entity, MANAGEMENT)[NAME]
    emulation_interface = find_interface(entity, EMULATION)
    emulation_ipv4 = format_address(emulation_interface, emulation_network)

    if entity_type is EntityType.SAT:
        return {
                'entity-type': entity_type.value,
                'ctrl-iface': management_interface,
                'emu-iface': emulation_interface[NAME],
                'emu-ipv4': emulation_ipv4,
                'platform-id': platform_id,
        }

    entity_id = entity[ID]
    lan_interface = find_item_with_regex(entity[IFACES], NETWORK, LAN)
    lan_name = lan_interface[NETWORK]
    lan_network = find_item_with_param(networks, NAME, lan_name)
    lan_ipv4 = format_address(lan_interface, lan_network)
    lan_ipv6 = format_address(lan_interface, lan_network, IPV6)

    return {
            'entity-type': entity_type.value,
            'ctrl-iface': management_interface,
            'emu-iface': emulation_interface[NAME],
            'emu-ipv4': emulation_ipv4,
            'platform-id': platform_id,
            'entity-id': entity_id,
            'lan-iface': lan_interface[NAME],
            'lan-ipv4': lan_ipv4,
            'lan-ipv6': lan_ipv6,
            'lan-name': lan_name,
    }


def configure_entities(scenario, topology):
    platform_id = topology[PLATFORM]
    for entity_type in EntityType:
        try:
            entities = find_items_with_param(topology[HOSTS], TYPE, entity_type.value)
            for entity in entities:
                name = entity[NAME]
                config = configure_entity(
                        scenario, entity, entity_type,
                        topology[NETWORKS], platform_id)
                lan_name = config.pop('lan-name', None)

                function = scenario.add_function('start_job_instance')
                function.configure('opensand_conf', name, offset=0, **config)

                if lan_name is not None:
                    yield lan_name, config['lan-ipv4'].split('/')[0]
        except (KeyError, ValueError):
            raise ValueError('Invalid {} host format'.format(entity_type.value))


def reset_entities(scenario, topology):
    for entity_type in EntityType:
        try:
            entities = find_items_with_param(topology[HOSTS], TYPE, entity_type.value)
            for entity in entities:
                name = entity[NAME]
                configuration = configure_entity(
                        scenario, entity, entity_type,
                        topology[NETWORKS], None)

                config = {
                        'entity-type': 'none',
                        'ctrl-iface': configuration['ctrl-iface'],
                        'emu-iface': configuration['emu-iface'],
                        'emu-ipv4': configuration['emu-ipv4'],
                }
                function = scenario.add_function('start_job_instance')
                function.configure('opensand_conf', name, offset=0, **config)

                if 'lan-name' in configuration:
                    yield configuration['lan-name'], configuration['lan-ipv4'].split('/')[0]
        except (KeyError, ValueError):
            raise ValueError('Invalid {} host format'.format(entity_type.value))


def build_opensand_scenario(scenario, topology, entities_handler, workstation_action):
    lans = dict(entities_handler(scenario, topology))

    for work_station in (host for host in topology[HOSTS] if TYPE not in host):
        name = work_station[NAME]
        for interface in work_station[IFACES]:
            lan_name = interface[NETWORK]
            if lan_name in lans:
                if workstation_action is WorkstationAction.ADD:
                    if_config = scenario.add_function('start_job_instance')
                    if_config.configure(
                            'ifconfig', name, offset=0,
                            interface_name=interface[NAME],
                            ip_address=interface[IPV4],
                            action=workstation_action.value)
                    wait_finished = [if_config]
                else:
                    wait_finished = []
                break
        else:
            raise ValueError('Invalid work-station format: no know lan network')

        try:
            lan_gateway = lans[lan_name]
            for network_name in lans:
                if network_name == lan_name:
                    continue

                network = find_item_with_param(topology[NETWORKS], NAME, network_name)
                network_address = network[IPV4][ADDRESS]
                network_netdigits = network[IPV4][NETDIGIT]
                destination = ipaddress.ip_network('{}/{}'.format(network_address, network_netdigits))

                function = scenario.add_function('start_job_instance', wait_finished=wait_finished)
                function.configure(
                        'ip_route', name, offset=0,
                        destination_ip=network_address,
                        subnet_mask=destination.netmask.exploded,
                        gateway_ip=lan_gateway,
                        action=workstation_action.value)
        except (KeyError, ValueError):
            raise ValueError('Invalid work-station host format')


def build_configure_scenario(topology, name='*** BUILT *** Configure OpenSAND platform'):
    scenario_configure = sb.Scenario(name, '')
    build_opensand_scenario(scenario_configure, topology, configure_entities, WorkstationAction.ADD)
    return scenario_configure


def build_reset_scenario(topology, name='*** BUILT *** Reset OpenSAND platform'):
    scenario_reset = sb.Scenario(name, '')
    build_opensand_scenario(scenario_reset, topology, reset_entities, WorkstationAction.DELETE)
    return scenario_reset


def build_emulation_scenario(topology, name='*** BUILT *** Run OpenSAND Emulation'):
    scenario = sb.Scenario(name, '')
    scenario.add_argument('opensand_scenario', 'The path to the OpenSAND scenario')

    function = scenario.add_function('start_job_instance')
    function.configure(
            'opensand_run', topology[OPENSAND_RUN], offset=0,
            **{
                'platform-id': topology[PLATFORM],
                'scenario-path': '$opensand_scenario',
            })

    return scenario


def topology(path):
    """Load topology from JSON file and quickly check integrity"""

    reader = FileType('r')
    with reader(path) as topology_file:
        try:
            data = json.load(topology_file)
        except ValueError as error:
            raise ArgumentTypeError("can't read json data from '{}': {}".format(path, error))

    try:
        data[HOSTS]
        networks = data[NETWORKS]
    except KeyError as error:
        raise ArgumentTypeError('missing topology data: \'{}\''.format(error))
    else:
        networks = {
                'management': find_items_with_param(networks, NAME, MANAGEMENT),
                'emulation': find_items_with_param(networks, NAME, EMULATION),
        }

    for name, network in networks.items():
        if not network:
            raise ArgumentTypeError('missing {} network description'.format(name))
        try:
            network, = network
        except ValueError:
            raise ArgumentTypeError('too many {} network description'.format(name))

        try:
            network[IPV4][NETDIGIT]
        except KeyError as error:
            raise ArgumentTypeError('missing {} network data: \'{}\''.format(name, error))

    return data
