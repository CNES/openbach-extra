from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.helpers.opensand import topology
from scenario_builder.scenarios import opensand_rate


def main(scenario_name='Metrology FAIRNESS TRANSPORT'):
    observer = ScenarioObserver()
    observer.add_scenario_argument(
            '--topology', type=topology, metavar='PATH',
            default='/home/exploit/topology.json',
            help='path to the JSON file describing the OpenSand topology')
    observer.add_scenario_argument(
            '--opensand-scenario', default='/home/exploit/.opensand/openbach/',
            help='path, on the OpenSand manager, to the scenario to run')
    observer.add_scenario_argument(
            '--post-processing', '--post-processing-entity',
            metavar='NAME', default='SAT',
            help='name of the entity to run post-processing jobs onto')
    observer.add_scenario_argument(
            '--client1', '--client1-entity', metavar='NAME', default='client1',
            help='name of the entity to act as client for performance jobs')
    observer.add_scenario_argument(
            '--client2', '--client2-entity', metavar='NAME', default='client2',
            help='name of the entity to act as client for performance jobs')
    observer.add_scenario_argument(
            '--server1', '--server1-entity', metavar='NAME', default='serverA',
            help='name of the entity to act as client for performance jobs')
    observer.add_scenario_argument(
            '--server2', '--server2-entity', metavar='NAME', default='serverB',
            help='name of the entity to act as server for performance jobs')
    observer.add_scenario_argument(
            '--gateway', '--gateway-entity',
            metavar='NAME', default='GW',
            help='name of the entity hosting the gateway to '
            'configure the one-way delay for performance tests')
    observer.add_scenario_argument(
            '--duration', '--tests-duration',
            type=int, metavar='TIME', default=10,
            help='duration in seconds of the analyze rate tests')
    observer.add_scenario_argument(
            '--file-size', metavar='SIZE', default='100M',
            help='size of the file to transfer during performance tests')
    observer.parse(default_scenario_name=scenario_name)

    scenario = opensand_rate.build(
            observer.args.topology,
            observer.args.opensand_scenario,
            observer.args.client1,
            observer.args.client2,
            observer.args.server1,
            observer.args.server2,
            observer.args.gateway,
            observer.args.post_processing,
            observer.args.duration,
            observer.args.file_size,
            observer.args.name,
    )
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
