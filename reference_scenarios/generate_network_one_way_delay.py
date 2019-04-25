from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_one_way_delay 

"""This script launches the *one_way_network_delay* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """

def main(scenario_name='generate_network_one_way_delay'):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', required=True,
            help='name of the entity for the client of the RTT tests')
    observer.add_scenario_argument(
            '--server', '--server-entity', required=True,
            help='name of the entity for the server of the owamp RTT test')
    observer.add_scenario_argument(
            '--ip_dst', required=True, help='server ip address and target of owamp test')
    observer.add_scenario_argument(
            '--entity_pp', help='The entity nama where the post-processing will be performed if defined')
       
    args = observer.parse(default_scenario_name=scenario_name)
    
    scenario = network_one_way_delay.build(
                      args.client, 
                      args.server, 
                      args.ip_dst, 
                      args.entity_pp, 
                      scenario_name)

    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
