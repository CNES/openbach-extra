from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.helpers.opensand import topology
from scenario_builder.scenarios import opensand_mptcp


def main(scenario_name='Measure Time'):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--topology', type=topology, metavar='PATH',
            default='/home/exploit/topology.json',
            help='path to the JSON file describing the OpenSand topology')
    observer.add_scenario_argument(
            '--opensand-scenario', default='/home/exploit/.opensand/openbach/',
            help='path, on the OpenSand manager, to the scenario to run')
    observer.add_scenario_argument(
            '--client', '--client-entity', default='Client',
            help='name of the entity for the client of socat tests')
    observer.add_scenario_argument(
            '--client-bandwidth', default='8M',
            help='the bandwidth allowed for the client on the terrestrial link')
    observer.add_scenario_argument(
            '--client-interfaces', nargs='+', default=['ens4', 'ens5'],
            help='interfaces to perform multipath on')
    observer.add_scenario_argument(
            '--client-terrestrial-interface',
            help='interface to use for the terrestrial link '
            '(default to the last entry of --client-interfaces)')
    observer.add_scenario_argument(
            '--server', '--server-entity', default='Server',
            help='name of the entity for the server of socat tests')
    observer.add_scenario_argument(
            '--server-bandwidth', default='20M',
            help='the bandwidth allowed for the server on the terrestrial link')
    observer.add_scenario_argument(
            '--server-interfaces', nargs='+', default=['ens4', 'ens5'],
            help='interfaces to perform multipath on')
    observer.add_scenario_argument(
            '--server-terrestrial-interface',
            help='interface to use for the terrestrial link '
            '(default to the last entry of --server-interfaces)')
    observer.add_scenario_argument(
            '--count', '--clients-count', type=int, default=1,
            help='amount of socat clients to launch')
    observer.add_scenario_argument(
            '--destination', '--destination-ip', default='127.0.0.1',
            help='the IP for the server to listen on '
            'and the clients to connect to')
    observer.add_scenario_argument(
            '--port', '--socat-port', type=int, default=7777,
            help='the port for the server to listen on '
            'and the clients to connect to')
    observer.add_scenario_argument(
            '--delay', '--terrestrial-delay', type=int, default=30,
            help='delay to apply on the terrestrial link between '
            'the server and the client')
    args = observer.parse(default_scenario_name=scenario_name)
    if args.server_terrestrial_interface is None:
        args.server_terrestrial_interface = args.server_interfaces[-1]
    if args.client_terrestrial_interface is None:
        args.client_terrestrial_interface = args.client_interfaces[-1]

    scenario = opensand_mptcp.build(
            args.topology, args.opensand_scenario,
            args.client, args.client_interfaces,
            args.client_terrestrial_interface, args.client_bandwidth,
            args.server, args.server_interfaces,
            args.server_terrestrial_interface, args.server_bandwidth,
            args.delay, args.count, args.destination, args.port, args.name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
