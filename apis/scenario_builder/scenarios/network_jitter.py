from scenario_builder import Scenario
from scenario_builder.helpers.transport.iperf3 import iperf3_rate_udp
from scenario_builder.helpers.network.owamp import owamp_measure_owd
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance



SCENARIO_DESCRIPTION="""This scenario allows to :
     - Launch the subscenario rate_tcp
       (allowing to compare the rate measurement of iperf3,
       and nuttcp jobs).
     - Perform two postprocessing tasks to compare the
       time-series and the CDF of the rate measurements.
"""

def extract_jobs_to_postprocess(scenario):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
            if function.job_name == 'owamp-client':
                yield function_id
            elif function.job_name == 'iperf3':
                if 'server' in function.start_job_instance['iperf3']:
                    yield function_id



def network_jitter(server, client, scenario_name='network_jitter'):
    scenario = Scenario(scenario_name, 'Comparison of jitter measurements with iperf3, owamp and D-ITG')
    scenario.add_argument('ip_dst', 'The destination IP for the clients')
    scenario.add_argument('port', 'The port of the server')
    scenario.add_argument('num_flows', 'The number of parallel flows to launch')
    scenario.add_argument('duration', 'The duration of each test (sec.)')
    scenario.add_argument('tos','the Type of service used')
    scenario.add_argument('bandwidth','the bandwidth of the measurement')

    wait = iperf3_rate_udp(scenario, server, client, '$ip_dst', '$port', '$num_flows', '$duration', '$tos', '$bandwidth')
    wait = owamp_measure_owd(scenario, server, client, '$ip_dst', wait) 
    
    return scenario

def build(client, server, ip_dst, port, num_flows, duration, tos, bandwidth, post_processing_entity, scenario_name):
    
    jitter_metrology = network_jitter(server, client)
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    start_jitter_metrology = scenario.add_function(
            'start_scenario_instance')
    start_jitter_metrology.configure(
            jitter_metrology,
            ip_dst=ip_dst,
            port=port,
            num_flows=num_flows,
            duration=duration,
            tos=tos,
            bandwidth=bandwidth)
    post_processed = [
            [start_jitter_metrology, function_id]
            for function_id in extract_jobs_to_postprocess(jitter_metrology)
    ]

    time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['jitter', 'ipdv_sent', 'ipdv_received', 'pdv_sent', 'pdv_received']], [['Jitter (ms)']], [['Comparison of Jitter measurements']], [start_jitter_metrology], None, 2)
    cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, [['jitter', 'ipdv_sent', 'ipdv_received', 'pdv_sent', 'pdv_received']], [['Jitter (ms)']], [['CDF of Jitter measurements']], [start_jitter_metrology], None, 2)

    return scenario
