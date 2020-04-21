"""Example of scenarios composition"""


from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_configure_link, service_data_transfer
from scenario_builder.helpers.transport.iperf3 import iperf3_find_server


def extract_iperf_statistic(job):
    data = job.statistics_data[('Flow1',)].dated_data
    return [
            (timestamp, stats['throughput'])
            for timestamp, stats in data.items()
    ]


def main(scenario_name='Configure Link & Data Download', argv=None):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--entity', '--configure-link-entity', '-e', required=True,
            help='Name of the entity where configure link should run')
    observer.add_scenario_argument(
            '--server', '--data-transfer-server', '-s', required=True,
            help='Name of the entity where the data transfer server should run')
    observer.add_scenario_argument(
            '--client', '--data-transfer-client', '-c', required=True,
            help='Name of the entity where the data transfer client should run')
    observer.add_scenario_argument(
            '--post-processing-entity',
            help='Name of the entity where the post-processing jobs should run')
    observer.add_scenario_argument(
            '--file-size', '--size', '-f', required=True,
            help='Size of the file transfer')
    observer.add_scenario_argument(
            '--duration', '-l', default=10, type=int,
            help='Duration of the file transfer')
    observer.add_scenario_argument(
            '--bandwidth-server-to-client', '-B', required=True,
            help='Bandwidth allocated for the server to answer the client')
    observer.add_scenario_argument(
            '--bandwidth-client-to-server', '-b', required=True,
            help='Bandwidth allocated for the client to ask the server')
    observer.add_scenario_argument(
            '--delay-server-to-client', '-D', required=True,
            help='Delay for a packet to go from the server to the client')
    observer.add_scenario_argument(
            '--delay-client-to-server', '-d', required=True,
            help='Delay for a packet to go from the client to the server')
    observer.add_scenario_argument(
            '--server-ip', '-I', required=True,
            help='IP of the server')
    observer.add_scenario_argument(
            '--client-ip', '-i', required=True,
            help='IP of the client')
    observer.add_scenario_argument(
            '--port', '-p', default=5201, type=int,
            help='Port used for the data transfer')
    observer.add_scenario_argument(
            '--middlebox-interfaces', '--interfaces', '-m', required=True,
            help='Comma-separated list of the network interfaces to emulate link on on the middlebox')

    args = observer.parse(argv, scenario_name)

    print('Clearing interfaces')
    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            'clear',
            args.bandwidth_server_to_client,
            args.delay_server_to_client)
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            'clear',
            args.bandwidth_client_to_server,
            args.delay_client_to_server)
    observer.launch_and_wait(scenario)

    print('Setting interfaces')
    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            'apply',
            args.bandwidth_server_to_client,
            args.delay_server_to_client)
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            'apply',
            args.bandwidth_client_to_server,
            args.delay_client_to_server)
    observer.launch_and_wait(scenario)

    print('Download', args.file_size, 'MB')
    scenario = service_data_transfer.build(
            args.server,
            args.client,
            args.duration,
            args.client_ip,
            args.port,
            args.file_size,
            0x04,
            1400,
            args.post_processing_entity)
    observer.launch_and_wait(scenario)

    results = DataProcessor(observer)
    results.add_callback('transfer', extract_iperf_statistic, *scenario.extract_function_id(iperf3=iperf3_find_server, include_subscenarios=True))
    data = results.post_processing()
    print('Results from data transfer:', data['transfer'])


    print('Clearing interfaces')
    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'ingress',
            'clear',
            args.bandwidth_server_to_client,
            args.delay_server_to_client)
    observer.launch_and_wait(scenario)

    scenario = network_configure_link.build(
            args.entity,
            args.middlebox_interfaces,
            'egress',
            'clear',
            args.bandwidth_client_to_server,
            args.delay_client_to_server)
    observer.launch_and_wait(scenario)
