from .. import Scenario
from ..helpers.traffic_and_metrics import owamp_measure_owd, fping_measure_rtt, hping_measure_rtt
from ..openbach_functions import StartJobInstance, StartScenarioInstance


SCENARIO_DESCRIPTION="""This scenario allows to :
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


def delay_simultaneous(client, server, scenario_name='Delay measurements - simultaneous'):
    scenario = Scenario(scenario_name, 'Comparison of three RTT measurements simultaneously')
    scenario.add_argument('ip_dst', 'Target of the pings and server IP adress')
    scenario.add_argument('duration', 'The duration of fping/hping tests')

    owamp_measure_owd(scenario, server, client, '$ip_dst')
    fping_measure_rtt(scenario, client, '$ip_dst', '$duration')
    hping_measure_rtt(scenario, client, '$ip_dst', '$duration')

    return scenario


def delay_sequential(client, server, scenario_name='Delay measurements - sequential'):
    scenario = Scenario(scenario_name, 'Comparison of three RTT measurements one after the other')
    scenario.add_argument('ip_dst', 'Target of the pings and server IP adress')
    scenario.add_argument('duration', 'The duration of fping/hping tests')

    wait = fping_measure_rtt(scenario, client, '$ip_dst', '$duration')
    wait = hping_measure_rtt(scenario, client, '$ip_dst', '$duration', wait)
    wait = owamp_measure_owd(scenario, server, client, '$ip_dst', wait)

    return scenario


def build(client, server, sequential, ip_dst, duration, post_processing_entity, scenario_name):              
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)                                                                  
    if sequential:                                                                                 
       delay_metrology = delay_sequential(client, server)                                          
    else:                                                                                          
       delay_metrology = delay_simultaneous(client, server)                                        
                                                                                                   
    start_delay_metrology = scenario.add_function(                                                 
            'start_scenario_instance')                                                             
                                                                                                   
    start_delay_metrology.configure(                                                               
            delay_metrology,                                                                       
            ip_dst=ip_dst,
            duration=duration)                                                                         
                                                                                                   
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
