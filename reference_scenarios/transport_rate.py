from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios.transport import rate_tcp 


def main(scenario_name='Rate metrology scenario'):
    """ Rate metrology scenario measuring network bandwidth with TCP flows 
        using nuttcp and iperf3 """
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', default='Client',
            help='name of the entity for the client iperf3/nuttcp')
    observer.add_scenario_argument(
            '--server', '--server-entity', default='Server',
            help='name of the entity for the server iperf3/nuttcp')
    #Argument of the scenario delay_simultaneous/delay_sequential and that is given by the 
    # function add_run() when the run action is chosen.
    observer.add_run_argument(
            'ip_dst', help='The server IP address')
    observer.add_run_argument(
            'port', help='The server IP port')
    observer.add_run_argument(
            'command_port', help='The port of nuttcp server for signalling')
    args = observer.parse(default_scenario_name=scenario_name)
    builder = rate_tcp
    scenario = builder(args.server, args.client, 30, 1, 0, 1000, args.name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
