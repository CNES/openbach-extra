from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_delay 

"""This script launches the *network_delay* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """

def main(scenario_name='Delay Metrology and Postprocessing'):
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
            '--ip_dst', help='server ip address and target of the pings')
    observer.add_scenario_argument(
            '--entity_pp', help='The entity nama where the post-processing will be performed')
       
    args = observer.parse(default_scenario_name=scenario_name)
    
    scenario = network_delay.build(
                      args.client, 
                      args.server, 
                      args.sequential, 
                      args.ip_dst, 
                      30, #duration of fping/hping tests (sec) 
                      args.entity_pp, 
                      scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
