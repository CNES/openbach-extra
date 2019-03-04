from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios.network import delay_simultaneous, delay_sequential


def main(scenario_name='Delay metrology scenario'):
    """This scenario allows to launch the delay_simultaneous or delay_sequential scenarios 
       allowing to compare the RTT measurement of fping, hping and owamp jobs."""
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
    #Argument of the scenario delay_simultaneous/delay_sequential and that is given by the 
    # function add_run() when the run action is chosen.
    observer.add_run_argument(
            'ip_dst', help='server ip address and target of the pings')
    args = observer.parse(default_scenario_name=scenario_name)

    builder = delay_sequential if args.sequential else delay_simultaneous
    scenario = builder(args.client, args.server, args.name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
