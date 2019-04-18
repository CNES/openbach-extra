from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios import network_jitter

"""This script launches the *network_jitter* scenario from /openbach-extra/apis/scenario_builder/scenarios/ """

def main(scenario_name='generate_network_jitter'):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--client', '--client-entity', default='Client',
            help='name of the entity for the client of the RTT tests')
    observer.add_scenario_argument(
            '--server', '--server-entity', default='Server',
            help='name of the entity for the server of the owamp RTT test')
    observer.add_scenario_argument(
            '--duration', default = 30,
            help='the duration of iperf3 test')
    observer.add_scenario_argument(
            '--bandwidth', default = '1M', 
            help='the bandwidth (bits/s) of iperf3 test')
    observer.add_scenario_argument(
            '--ip_dst', required=True, help='server ip address and target of the pings')
    observer.add_scenario_argument(
            '--port', default = 7000, help='the iperf3 server port for data')
    observer.add_scenario_argument(
            '--entity_pp', default='Client', help='The entity where the post-processing will '
            'be performed (histogtram/time-series jobs must be installed)')

    args = observer.parse(default_scenario_name=scenario_name)

    scenario = network_jitter.build(
                      args.client,
                      args.server,
                      args.ip_dst,
                      args.port,
                      1,
                      args.duration,
                      0,
                      args.bandwidth,
                      args.entity_pp,
                      args.name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()

