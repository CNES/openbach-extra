from .. import Scenario
from ..helpers.traffic_and_metrics import iperf3_rate_tcp, nuttcp_rate_tcp
from ..openbach_functions import StartJobInstance, StartScenarioInstance



"""This scenario allows to :
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



def rate_tcp(server, client, scenario_name='Rate metrology with tcp flows'):
    scenario = Scenario(scenario_name, 'Rate metrology scenario measuring network bandwidth with TCP flows')
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
    scenario = Scenario(
            scenario_name,
            'Rate metrology scenario measuring network bandwidth with TCP flows '
            'using nuttcp and iperf3')

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

    time_series = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_rate_metrology],
            wait_delay=2)
    time_series.configure(
            'time_series', post_processing_entity, offset=0,
            jobs=[post_processed],
            statistics=[['rate', 'throughput']],
            label=[['Rate (b/s)']],
            title=[['Comparison of Rate measurements']])

    histograms = scenario.add_function(
            'start_job_instance',
            wait_finished=[start_rate_metrology],
            wait_delay=2)
    histograms.configure(
            'histogram', post_processing_entity, offset=0,
            jobs=[post_processed],
            bins=100,
            statistics=[['rate', 'throughput']],
            label=['Rate (b/s)'],
            title=['CDF of Rate measurements'],
            cumulative=True)


    return scenario
