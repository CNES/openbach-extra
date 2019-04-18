from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_delay 

"""This script launches the *network_delay* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """

def main(scenario_name='generate_network_delay'):
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
    observer.add_scenario_argument(
            '--ip_dst', required=True, help='server ip address and target of the pings')
    observer.add_scenario_argument(
            '--duration', default=10, help='duration of delay scenario (s)')
    observer.add_scenario_argument(
            '--entity_pp', default='Client', help='The entity where the post-processing will '
            'be performed (histogtram/time-series jobs must be installed)')
       
    args = observer.parse(default_scenario_name=scenario_name)
    
    scenario = network_delay.build(
                      args.client, 
                      args.server, 
                      args.sequential, 
                      args.ip_dst, 
                      args.duration, 
                      args.entity_pp, 
                      scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
