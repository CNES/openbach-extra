from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import transport_rate 

"""This scenario allows to :                                         
     - Launch the subscenario rate_tcp 
       (allowing to compare the rate measurement of iperf3,            
       and nuttcp jobs).                                        
     - Perform two postprocessing tasks to compare the               
       time-series and the CDF of the rate measurements.            
"""                                                                  


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
    observer.add_scenario_argument(
            '--ip_dst', help='The server IP address')
    observer.add_scenario_argument(
            '--port', help='The server IP port')
    observer.add_scenario_argument(
            '--command_port', help='The port of nuttcp server for signalling')
    observer.add_scenario_argument(
            '--entity_pp', help='The entity nama where the post-processing will be performed')
     
    args = observer.parse(default_scenario_name=scenario_name)
    scenario = transport_rate.build(
            args.client, 
            args.server, 
            args.ip_dst, 
            args.port, 
            args.command_port, 
            args.entity_pp, 
            30, #duration 
            1, #number of parallel flows
            0, #ToS
            1000-40, #MTU size
            args.name)
    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
