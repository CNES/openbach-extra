from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_rate 

"""This scenario launches the *network_rate* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """                                         

def main(scenario_name='generate_network_rate'):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', default='Client',
            help='name of the entity for the client iperf3/nuttcp')
    observer.add_scenario_argument(
            '--server', '--server-entity', default='Server',
            help='name of the entity for the server iperf3/nuttcp')
    observer.add_scenario_argument(
            '--ip_dst', required=True, help='The server IP address')
    observer.add_scenario_argument(
            '--port', default = 7000,  help='The iperf3/nuttcp server port for data')
    observer.add_scenario_argument(
            '--rate', help='Set a higher rate (in kb/s) than what you estimate between server and client '
            'for the UDP test (add m/g to set M/G b/s)', required=True)
    observer.add_scenario_argument(
            '--command_port', default = 8000, help='The port of nuttcp server for signalling')
    observer.add_scenario_argument(
            '--entity_pp', default='Client', help='The entity where the post-processing will be performed '
            '(histogtram/time-series jobs must be installed)')
     
    args = observer.parse(default_scenario_name=scenario_name)
    scenario = network_rate.build(
            args.client, 
            args.server, 
            args.ip_dst, 
            args.port, 
            args.command_port, 
            args.rate,
            args.entity_pp, 
            30, #duration of iperf/nuttcp tests
            1, #number of parallel flows
            0, #ToS
            1000-40, #MTU size
            args.name)
    observer.launch_and_wait(scenario)

if __name__ == '__main__':
    main()
