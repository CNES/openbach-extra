import itertools

from scenario_observer import ScenarioConstructor

import scenario_builder as sb
from scenario_builder.openbach_functions import StartJobInstance
from lib.opensand import (
        topology as topology_loader,
        find_host_by_name, find_common_lan_network,
        build_configure_scenario, build_emulation_scenario,
)
from lib.metrics import (
        configure_one_way_delays, analyse_one_way_delay,
        analyse_rate, analyse_performances,
)


DELAYS = (10,)
CONGESTION_CONTROLS = (
        ('bbr', 'bbr'),
        ('cubic', 'cubic'),
        ('cubic', 'bbr'),
)


class ScenarioObserver(ScenarioConstructor):
    def build_parser(self):
        group = super().build_parser()
        group.add_argument(
                '--topology', type=topology_loader, metavar='PATH',
                default='/home/exploit/topology.json',
                help='path to the JSON file describing the OpenSand topology')
        group.add_argument(
                '--opensand-scenario', default='/home/exploit/.opensand/openbach/',
                help='path, on the OpenSand manager, to the scenario to run')
        group.add_argument(
                '--post-processing', '--post-processing-entity',
                metavar='NAME', default='SAT',
                help='name of the entity to run post-processing jobs onto')
        group.add_argument(
                '--client1', '--client1-entity', metavar='NAME', default='client1',
                help='name of the entity to act as client for performance jobs')
        group.add_argument(
                '--client2', '--client2-entity', metavar='NAME', default='client2',
                help='name of the entity to act as client for performance jobs')
        group.add_argument(
                '--server1', '--server1-entity', metavar='NAME', default='serverA',
                help='name of the entity to act as client for performance jobs')
        group.add_argument(
                '--server2', '--server2-entity', metavar='NAME', default='serverB',
                help='name of the entity to act as server for performance jobs')
        group.add_argument(
                '--gateway', '--gateway-entity',
                metavar='NAME', default='GW',
                help='name of the entity hosting the gateway to '
                'configure the one-way delay for performance tests')
        group.add_argument(
                '--duration', '--tests-duration',
                type=int, metavar='TIME', default=10,
                help='duration in seconds of the analyze rate tests')
        group.add_argument(
                '--file-size', metavar='SIZE', default='100M',
                help='size of the file to transfer during performance tests')


def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'owamp-client':
                yield function_id
            elif function.job_name == 'nuttcp':
                if 'client' in function.start_job_instance['nuttcp']:
                    yield function_id
            elif function.job_name == 'iperf3':
                if 'server' in function.start_job_instance['iperf3']:
                    yield function_id


def build_metrology_scenario(
        client1, client2, server1, server2, gateway,
        rate_test_duration, transfered_file_size):
    scenario = sb.Scenario(
            'QoS metrics',
            'This scenario analyse the path between server and client in '
            'terms of maximum data rate (b/s) and one-way delay (s)')
    scenario.add_constant('com_port', '6000')
    scenario.add_constant('udp_rate', '30M')
    scenario.add_constant('duration', str(rate_test_duration))
    scenario.add_constant('file_size', transfered_file_size)
    scenario.add_argument('port', 'The port of the nuttcp/iperf3 server')
    scenario.add_argument('dest_ip_server_A', 'ServerA IP')
    scenario.add_argument('dest_ip_server_B', 'ServerB IP')
    scenario.add_argument('interface_server_A', 'Iface of serverA')
    scenario.add_argument('interface_server_B', 'Iface of serverB')
    scenario.add_argument('interface_gateway', 'Iface of GW to LAN')

    configurations = itertools.product(DELAYS, CONGESTION_CONTROLS)
    wait_finished = []
    for delay, (congestionA, congestionB) in configurations:
        work_stations = {
                server1: ('$interface_server_A', congestionA),
                server2: ('$interface_server_B', congestionB),
        }
        wait = configure_one_way_delays(
                scenario, delay, gateway, '$interface_gateway',
                wait_finished=wait_finished, **work_stations)
        wait = analyse_rate(
                scenario, server1, client1, '$com_port',
                '$dest_ip_server_A', '$port', 'False',
                '$duration', '$udp_rate', wait, wait_delay=2)
        wait = analyse_one_way_delay(
                scenario, server1, client1,
                '$dest_ip_server_A', wait)
        wait_finished = analyse_performances(
                scenario, server1, client1, '$port',
                '$dest_ip_server_A', '$file_size',
                wait, wait_delay=2)
        wait_finished.extend(analyse_performances(
                scenario, server2, client2, '$port',
                '$dest_ip_server_B', '$file_size',
                wait, wait_delay=2))

    return scenario


def main(project_name='rate_jobs', scenario_name='Metrology FAIRNESS TRANSPORT'):
    observer = ScenarioObserver()
    observer.parse()
    if not observer.args.project:
        observer.args.project = project_name
    if not observer.args.name:
        observer.args.name = scenario_name

    topology = observer.args.topology
    configure_opensand = build_configure_scenario(topology)
    opensand_emulation = build_emulation_scenario(topology)
    client1 = observer.args.client1
    client2 = observer.args.client2
    server1 = observer.args.server1
    server2 = observer.args.server2
    gateway_entity = observer.args.gateway
    metrology_scenario = build_metrology_scenario(
            client1, client2, server1, server2,
            gateway_entity,
            observer.args.duration,
            observer.args.file_size)

    scenario = sb.Scenario(
            observer.args.name,
            'This scenario aims at comparing the fairness and '
            'performance of two congestion controls for different '
            'SATCOM system characteristics.')

    start_configure = scenario.add_function('start_scenario_instance')
    start_configure.configure(configure_opensand)

    start_emulation = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_configure],
            wait_delay=10)
    start_emulation.configure(
            opensand_emulation,
            opensand_scenario=observer.args.opensand_scenario)

    gateway = find_host_by_name(topology, gateway_entity)
    serverA = find_host_by_name(topology, server1)
    serverB = find_host_by_name(topology, server2)
    lan_gateway, lan_serverA, lan_serverB = find_common_lan_network(gateway, serverA, serverB)
    start_metrology = scenario.add_function(
            'start_scenario_instance',
            wait_launched=[start_emulation],
            wait_delay=30)
    start_metrology.configure(
            metrology_scenario,
            port=7000,
            dest_ip_server_A=lan_serverA['ipv4'],
            dest_ip_server_B=lan_serverB['ipv4'],
            interface_server_A=lan_serverA['name'],
            interface_server_B=lan_serverB['name'],
            interface_gateway=lan_gateway['name'])

    entity = observer.args.post_processing
    post_processed = [
            [start_metrology, function_id]
            for function_id in extract_jobs_to_postprocess(metrology_scenario)
    ]

    time_series = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_metrology],
            wait_delay=2)
    time_series.configure(
            'time_series', entity, offset=0,
            jobs=[post_processed],
            statistics=[['rate'], ['owd_sent'], ['throughput']],
            label=[['Transmitted data (bits)'], ['OWD (sec)'], ['Throughput (b/s)']],
            title=[['Validation of rate'], ['Validation of OWD'], ['Throughput Comparison']])

    histograms = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_metrology],
            wait_delay=2)
    histograms.configure(
            'histogram', entity, offset=0,
            jobs=[post_processed],
            bins=100,
            statistics=[['sent_data']],
            label=['Transmitted data (bits)'],
            title=['CDF of transmitted data'],
            cumulative=True)

    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
