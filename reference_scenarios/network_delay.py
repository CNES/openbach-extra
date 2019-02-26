from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios.network import delay, delay_sequential


def main(scenario_name='Delay metrology scenario'):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', default='Client',
            help='name of the entity for the client of the RTT tests')
    observer.add_scenario_argument(
            '--server', '--server-entity', default='Server',
            help='name of the entity for the server of the owamp RTT test')
    observer.add_scenario_argument(
            '--sequential', action='store_true',
            help='whether or not the test should run one after the other')
    args = observer.parse(default_scenario_name=scenario_name)

    builder = delay_sequential if args.sequential else delay
    scenario = builder(args.client, args.server, args.name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
