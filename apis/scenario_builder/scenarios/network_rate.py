from scenario_builder import Scenario
from scenario_builder.helpers.transport.iperf3 import iperf3_rate_tcp
from scenario_builder.helpers.transport.nuttcp import nuttcp_rate_tcp
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
            if function.job_name == 'nuttcp':
                if 'client' in function.start_job_instance['nuttcp']:
                    yield function_id
            elif function.job_name == 'iperf3':
                if 'server' in function.start_job_instance['iperf3']:
                    yield function_id



def rate_tcp(server, client, scenario_name='network_rate'):
    scenario = Scenario(scenario_name, 'Comparison of rate measurements with TCP flows, by means of iperf3/nuttcp')
    scenario.add_argument('ip_dst', 'The destination IP for the clients')
    scenario.add_argument('port', 'The port of the server')
    scenario.add_argument('command_port', 'The port of nuttcp server for signalling')
    scenario.add_argument('duration', 'The duration of each test (sec.)')
    scenario.add_argument('num_flows', 'The number of parallel flows to launch')
    scenario.add_argument('tos', 'The duration of each test (sec.)')
    scenario.add_argument('mtu', 'The MTU sizes to test')
    

    wait = iperf3_rate_tcp(scenario, server, client, '$ip_dst', '$port', '$duration', '$num_flows', '$tos', '$mtu')
    nuttcp_rate_tcp(scenario, server, client, '$ip_dst', '$port', '$command_port', '$duration', '$num_flows', '$tos', '$mtu', wait)
    
    return scenario

def build(client, server, ip_dst, port, command_port, post_processing_entity, duration, num_flows, tos, mtu, scenario_name):
    
    rate_metrology = rate_tcp (server, client)
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)

    start_rate_metrology = scenario.add_function(
            'start_scenario_instance')
    start_rate_metrology.configure(
            rate_metrology,
            ip_dst=ip_dst, port=port,
            command_port=command_port,
            duration=duration, num_flows=num_flows,
            tos=tos, mtu=mtu)
    post_processed = [
            [start_rate_metrology, function_id]
            for function_id in extract_jobs_to_postprocess(rate_metrology)
    ]

    time_series_on_same_graph(scenario, post_processing_entity, post_processed, [['rate', 'throughput']], [['Rate (b/s)']], [['Comparison of Rate measurements']], [start_rate_metrology], None, 2)
    cdf_on_same_graph(scenario, post_processing_entity, post_processed, 100, [['rate', 'throughput']], [['Rate (b/s)']], [['CDF of Rate measurements']], [start_rate_metrology], None, 2)

    return scenario
