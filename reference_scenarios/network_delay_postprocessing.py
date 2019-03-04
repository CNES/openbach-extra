from scenario_builder import Scenario
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance
from auditorium_scripts.scenario_observer import ScenarioObserver
from scenario_builder.scenarios.network import delay_simultaneous, delay_sequential

"""This scenario allows to :
     - Launch the subscenarios delay_simultaneous or delay_sequential 
       (allowing to compare the RTT measurement of fping, 
       hping and owamp jobs).
     - Perform two postprocessing tasks to compare the 
       time-series and the CDF of the delay measurements.
"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'owamp-client':
                yield function_id
            elif function.job_name == 'hping':
                yield function_id
            elif function.job_name == 'fping':
                yield function_id

def build(client, server, sequential, ip_dst, post_processing_entity, scenario_name):
    
    if sequential:
       delay_metrology = delay_sequential(client, server) 
    else:
       delay_metrology = delay_simultaneous(client, server)
    
    scenario = Scenario(
            scenario_name,
            'This scenario aims at comparing the measured delay '
            'of three jobs that measure the RTT in a different way.')

    start_delay_metrology = scenario.add_function(
            'start_scenario_instance')

    start_delay_metrology.configure(
            delay_metrology,
            ip_dst=ip_dst)

    post_processed = [
            [start_delay_metrology, function_id]
            for function_id in extract_jobs_to_postprocess(delay_metrology)
    ]

    time_series = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_delay_metrology],
            wait_delay=2)
    time_series.configure(
            'time_series', post_processing_entity, offset=0,
            jobs=[post_processed],
            statistics=[['rtt', 'owd_sent']],
            label=[['RTT delay (ms)']],
            title=[['Comparison of RTT']])

    histograms = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_delay_metrology],
            wait_delay=2)
    histograms.configure(
            'histogram', post_processing_entity, offset=0,
            jobs=[post_processed],
            bins=100,
            statistics=[['rtt', 'owd_sent']],
            label=['RTT delay (ms)'],
            title=['CDF of RTT delay measurements'],
            cumulative=True)


    return scenario

def main(scenario_name='RTT mesurements and postprocessing'):
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
    
    scenario = build(args.client, args.server, args.sequential, args.ip_dst, args.entity_pp, scenario_name)
    observer.launch_and_wait(scenario)


if __name__ == '__main__':
    main()
