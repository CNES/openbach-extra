from scenario_builder import Scenario
from scenario_builder.helpers.network.fping import fping_measure_rtt
from scenario_builder.helpers.network.hping import hping_measure_rtt
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance


SCENARIO_DESCRIPTION="""This scenario allows to :
     - Launch the subscenarios delay_simultaneous or delay_sequential
       (allowing to compare the RTT measurement of fping (ICMP),
       hping (TCP SYN ACK) ).
     - Perform two postprocessing tasks to compare the
       time-series and the CDF of the delay measurements.
"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'fping':
                yield function_id
            elif function.job_name == 'hping':
                yield function_id


def delay_simultaneous(client, scenario_name='network_delay_simultaneous'):
    scenario = Scenario(scenario_name, 'OpenBACH Network Delay Measurement: Comparison of two RTT measurements simultaneously')
    scenario.add_argument('ip_dst', 'Target of the pings and server IP adress')
    scenario.add_argument('duration', 'The duration of fping/hping tests')

    fping_measure_rtt(scenario, client, '$ip_dst', '$duration')
    hping_measure_rtt(scenario, client, '$ip_dst', '$duration')

    return scenario


def delay_sequential(client, scenario_name='network_delay_sequential'):
    scenario = Scenario(scenario_name, 'OpenBACH Network Delay Measurement: Comparison of two RTT measurements one after the other')
    scenario.add_argument('ip_dst', 'Target of the pings and server IP adress')
    scenario.add_argument('duration', 'The duration of each fping/hping tests')

    wait = fping_measure_rtt(scenario, client, '$ip_dst', '$duration')
    wait = hping_measure_rtt(scenario, client, '$ip_dst', '$duration', wait)

    return scenario


def build(client, ip_dst, duration, simultaneous, post_processing_entity, scenario_name):              
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)                                                                  
    if simultaneous:                                                                                 
       delay_metrology = delay_simultaneous(client)                                        
    else:                                                                                          
       delay_metrology = delay_sequential(client)                                          
                                                                                                   
    start_delay_metrology = scenario.add_function(                                                 
            'start_scenario_instance')                                                             
                                                                                                   
    start_delay_metrology.configure(                                                               
            delay_metrology,                                                                       
            ip_dst=ip_dst,
            duration=duration)                                                                         
    if post_processing_entity is not None:
       post_processed = [                                                                             
            [start_delay_metrology, function_id]                                                   
            for function_id in extract_jobs_to_postprocess(delay_metrology)                        
       ]                                                                                              
       time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['rtt']], [['RTT delay (ms)']], [['Comparison of measured RTTs']], [start_delay_metrology], None, 2)
       cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, [['rtt']], [['RTT delay (ms)']], [['CDF of RTT delay measurements']], [start_delay_metrology], None, 2)

    return scenario                                   
