import itertools

from scenario_observer import ScenarioObserver

import scenario_builder as sb
from scenario_builder.openbach_functions import StartJobInstance
from lib.opensand import (
        topology as topology_loader, find_work_stations_on_network,
        find_a_gateway, find_a_lan_network,
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


def build_metrology_scenario(client1, client2, server1, server2, gateway, terminal):
    scenario = sb.Scenario(
            'QoS metrics',
            'This scenario analyse the path between server and client in '
            'terms of maximum data rate (b/s) and one-way delay (s)')
    scenario.add_constant('com_port', '6000')  # The port of nuttcp server for signalling
    scenario.add_constant('duration', '10')    # The duration of each test (sec.)
    scenario.add_constant('udp_rate', '30M')   # The port of nuttcp server for signalling
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
                '$dest_ip_server_A', '100M', wait, wait_delay=2)
        wait_finished.extend(analyse_performances(
                scenario, server2, client2, '$port',
                '$dest_ip_server_B', '100M', wait, wait_delay=2))

    return scenario


def main(project_name='rate_jobs', scenario_name='Metrology FAIRNESS TRANSPORT'):
    topology = topology_loader('/home/exploit/openbach-extra/scenario_examples/rate_scenario/topology.json')
    configure_opensand = build_configure_scenario(topology)
    opensand_emulation = build_emulation_scenario(topology)
    metrology_scenario = build_metrology_scenario('client', 'client2', 'serverA', 'serverB', 'GW', 'ST')

    scenario = sb.Scenario(
            scenario_name,
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
            opensand_scenario='/home/exploit/.opensand/recette_openbach')

    gateway = find_a_gateway(topology)
    gateway_lan = find_a_lan_network(gateway)
    serverA, serverB, *_ = find_work_stations_on_network(topology, gateway_lan)
    start_metrology = scenario.add_function(
            'start_scenario_instance',
            wait_launched=[start_emulation],
            wait_delay=30)
    start_metrology.configure(
            metrology_scenario,
            port=7000,
            dest_ip_server_A=serverA['ipv4'],
            dest_ip_server_B=serverB['ipv4'],
            interface_server_A=serverA['name'],
            interface_server_B=serverB['name'],
            interface_gateway=gateway_lan['name'])

    post_processed = [
            [start_metrology, function_id]
            for function_id in extract_jobs_to_postprocess(metrology_scenario)
    ]

    time_series = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_metrology],
            wait_delay=2)
    time_series.configure(
            'time_series', 'SAT', offset=0,
            jobs=[post_processed],
            statistics=[['rate'], ['owd_sent'], ['throughput']],
            label=[['Transmitted data (bits)'], ['OWD (sec)'], ['Throughput (b/s)']],
            title=[['Validation of rate'], ['Validation of OWD'], ['Throughput Comparison']])

    histograms = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_metrology],
            wait_delay=2)
    histograms.configure(
            'histogram', 'SAT', offset=0,
            jobs=[post_processed],
            bins=100,
            statistics=[['sent_data']],
            label=['Transmitted data (bits)'],
            title=['CDF of transmitted data'],
            cumulative=True)

    observer = ScenarioObserver(scenario_name, project_name, scenario)
    observer.launch_and_wait()


if __name__ == '__main__':
    main()
