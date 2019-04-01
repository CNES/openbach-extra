from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_rate 

"""This scenario launches the *network_rate* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """                                         

def main(scenario_name='Rate Metrology and Postprocessing'):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', default='Client',
            help='name of the entity for the client iperf3/nuttcp')
    observer.add_scenario_argument(
            '--server', '--server-entity', default='Server',
            help='name of the entity for the server iperf3/nuttcp')
    observer.add_scenario_argument(
            '--ip_dst', help='The server IP address')
    observer.add_scenario_argument(
            '--port', help='The server IP port')
    observer.add_scenario_argument(
            '--command_port', help='The port of nuttcp server for signalling')
    observer.add_scenario_argument(
            '--entity_pp', help='The entity nama where the post-processing will be performed')
     
    args = observer.parse(default_scenario_name=scenario_name)
    scenario = network_rate.build(
            args.client, 
            args.server, 
            args.ip_dst, 
            args.port, 
            args.command_port, 
            args.entity_pp, 
            30, #duration of iperf/nuttcp tests
            1, #number of parallel flows
            0, #ToS
            1000-40, #MTU size
            args.name)
    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
