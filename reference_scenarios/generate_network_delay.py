from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_delay 

"""This script launches the *network_delay* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """

def main(scenario_name='generate_network_delay'):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', required=True,
            help='name of the entity for the client of the RTT tests')
    observer.add_scenario_argument(
            '--ip_dst', required=True, help='server ip address and target of the pings')
    observer.add_scenario_argument(
            '--duration', default=10, help='duration of delay scenario (s)')
    observer.add_scenario_argument(
            '--simultaneous', action='store_true',
            help='option whether or not the test is simultaneous. Default sequential')
    observer.add_scenario_argument(
            '--entity_pp',  help='The entity where the post-processing will '
            'be performed (histogram/time-series jobs must be installed) if defined')
       
    args = observer.parse(default_scenario_name=scenario_name)
    
    scenario = network_delay.build(
                      args.client, 
                      args.ip_dst, 
                      args.duration, 
                      args.simultaneous, 
                      args.entity_pp, 
                      scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
