from auditorium_scripts.scenario_observer import ScenarioConstructor
from scenario_builder.scenarios.network import delay, delay_sequential


class ScenarioObserver(ScenarioConstructor):
    def build_parser(self):
        group = super().build_parser()
        group.add_argument(
                '--client', '--client-entity', default='Client',
                help='name of the entity for the client of the RTT tests')
        group.add_argument(
                '--server', '--server-entity', default='Server',
                help='name of the entity for the server of the owamp RTT test')
        group.add_argument(
                '--sequential', action='store_true',
                help='whether or not the test should run one after the other')


def main():
    observer = ScenarioObserver()
    observer.parse()

    builder = delay_sequential if observer.args.sequential else delay
    scenario = builder(observer.args.client, observer.args.server)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
