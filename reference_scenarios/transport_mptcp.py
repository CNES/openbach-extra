from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios.transport import send_file_tcp


def main(scenario_name='Measure Time'):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', default='Client',
            help='name of the entity for the client of socat tests')
    observer.add_scenario_argument(
            '--server', '--server-entity', default='Server',
            help='name of the entity for the server of socat tests')
    observer.add_scenario_argument(
            '--count', '--clients-count', type=int, default=1,
            help='amount of socat clients to launch')
    observer.add_run_argument('filesize')
    observer.add_run_argument('dest_ip')
    observer.add_run_argument('port')
    args = observer.parse(default_scenario_name=scenario_name)

    scenario = send_file_tcp(args.server, args.client, args.count, args.name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
