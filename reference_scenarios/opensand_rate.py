from auditorium_scripts.scenario_observer import ScenarioConstructor
from scenario_builder.helpers.opensand import topology
from scenario_builder.scenarios import opensand_rate


class ScenarioObserver(ScenarioConstructor):
    def build_parser(self):
        group = super().build_parser()
        group.add_argument(
                '--topology', type=topology, metavar='PATH',
                default='/home/exploit/topology.json',
                help='path to the JSON file describing the OpenSand topology')
        group.add_argument(
                '--opensand-scenario', default='/home/exploit/.opensand/openbach/',
                help='path, on the OpenSand manager, to the scenario to run')
        group.add_argument(
                '--post-processing', '--post-processing-entity',
                metavar='NAME', default='SAT',
                help='name of the entity to run post-processing jobs onto')
        group.add_argument(
                '--client1', '--client1-entity', metavar='NAME', default='client1',
                help='name of the entity to act as client for performance jobs')
        group.add_argument(
                '--client2', '--client2-entity', metavar='NAME', default='client2',
                help='name of the entity to act as client for performance jobs')
        group.add_argument(
                '--server1', '--server1-entity', metavar='NAME', default='serverA',
                help='name of the entity to act as client for performance jobs')
        group.add_argument(
                '--server2', '--server2-entity', metavar='NAME', default='serverB',
                help='name of the entity to act as server for performance jobs')
        group.add_argument(
                '--gateway', '--gateway-entity',
                metavar='NAME', default='GW',
                help='name of the entity hosting the gateway to '
                'configure the one-way delay for performance tests')
        group.add_argument(
                '--duration', '--tests-duration',
                type=int, metavar='TIME', default=10,
                help='duration in seconds of the analyze rate tests')
        group.add_argument(
                '--file-size', metavar='SIZE', default='100M',
                help='size of the file to transfer during performance tests')


def main():
    observer = ScenarioObserver()
    observer.parse()

    scenario = opensand_rate.build(
            observer.args.name,
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
    )
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
