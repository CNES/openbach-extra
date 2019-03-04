import itertools

from .. import Scenario
from ..openbach_functions import StartJobInstance
from ..scenarios.opensand import build_configure_scenario, build_emulation_scenario
from ..helpers.opensand import find_host_by_name, find_common_lan_network
from ..helpers.traffic_and_metrics import (
        owamp_measure_owd,
        nuttcp_rate_udp,
        iperf3_send_file_tcp,
)
from ..helpers.configuration import (
        configure_one_way_delays,



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


def build_metrology_scenario(
        client1, client2, server1, server2, gateway,
        rate_test_duration, transfered_file_size,
        scenario_name='QoS metrics'):
    scenario = Scenario(
            scenario_name,
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
        wait = nuttcp_rate_udp(
                scenario, server1, client1, '$com_port',
                '$dest_ip_server_A', '$port', 'False',
                '$duration', '$udp_rate', wait, wait_delay=2)
        wait = owamp_measure_owd(
                scenario, server1, client1,
                '$dest_ip_server_A', wait)
        wait_finished = iperf3_send_file_tcp(
                scenario, server1, client1, '$port',
                '$dest_ip_server_A', '$file_size',
                wait, wait_delay=2)
        wait_finished.extend(iperf3_send_file_tcp(
                scenario, server2, client2, '$port',
                '$dest_ip_server_B', '$file_size',
                wait, wait_delay=2))

    return scenario


def build(
        topology, opensand_scenario,
        client1, client2, server1, server2,
        gateway_entity, post_processing_entity,
        duration=10, file_size='100M',
        scenario_name='Metrology Fairness Transport'):
    configure_opensand = build_configure_scenario(topology)
    opensand_emulation = build_emulation_scenario(topology)
    metrology_scenario = build_metrology_scenario(
            client1, client2, server1, server2,
            gateway_entity, duration, file_size)

    scenario = Scenario(
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
            opensand_scenario=opensand_scenario)

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

    post_processed = [
            [start_metrology, function_id]
            for function_id in extract_jobs_to_postprocess(metrology_scenario)
    ]

    time_series = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_metrology],
            wait_delay=2)
    time_series.configure(
            'time_series', post_processing_entity, offset=0,
            jobs=[post_processed],
            statistics=[['rate'], ['owd_sent'], ['throughput']],
            label=[['Transmitted data (bits)'], ['OWD (sec)'], ['Throughput (b/s)']],
            title=[['Validation of rate'], ['Validation of OWD'], ['Throughput Comparison']])

    histograms = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_metrology],
            wait_delay=2)
    histograms.configure(
            'histogram', post_processing_entity, offset=0,
            jobs=[post_processed],
            bins=100,
            statistics=[['sent_data']],
            label=['Transmitted data (bits)'],
            title=['CDF of transmitted data'],
            cumulative=True)

    stop_opensand = scenario.add_function(
            'stop_scenario_instance',
            wait_finished=[time_series, histograms])
    stop_opensand.configure(start_emulation)

    return scenario
