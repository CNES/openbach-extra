from scenario_builder import Scenario
import scenario_builder.scenarios.transport_configuration_tcp_stack as transport_configuration_tcp_stack
import scenario_builder.scenarios.configure_link as configure_link
import scenario_builder.scenarios.rate_monitoring as rate_monitoring
import scenario_builder.scenarios.service_traffic_mix as service_traffic_mix
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance
import enum
import itertools
from collections import defaultdict


SCENARIO_DESCRIPTION="""This scenario allows to :
     - Launch {0} tests
     - Under various network conditions including losses and congestion
     - For differents tcp configurations.
"""
SUBSCENARIO_NAME="""Launch {0} tests under following network conditions: loss={1}, congestion={2}"""
SUBSCENARIO_DESCRIPTION = """Launch {} tests for different tcp configurations and traffics"""


class TrafficType(enum.Enum):
      MIX='mix'
      WEB_BROWSING='web_browsing'
      DASH='dash'
      BACKGROUND='background'

def extract_jobs_to_postprocess_recursively(scenario, job_name, hierarchies=[]):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
           if function.job_name == job_name and job_name == 'iperf3':
                if 'server' in function.start_job_instance['iperf3']:
                   yield hierarchies + [function_id]
           elif function.job_name == job_name:
              yield hierarchies + [function_id]
        elif isinstance(function, StartScenarioInstance) and isinstance(function.scenario_name, Scenario):
             if job_name == 'rate_monitoring':
                print(hierarchies + [function_id])
             yield from extract_jobs_to_postprocess_recursively(function.scenario_name, job_name, hierarchies + [function_id]) 

def compute_tcp_confs(traffic_type, ccs_web_browsing, ccs_dash, initcwnds):
    if traffic_type is TrafficType.MIX:
       # Compute tcp configurations to apply on both web and dash server
       tcp_configurations = list(itertools.product(ccs_web_browsing, ccs_dash, initcwnds))
    elif traffic_type is TrafficType.WEB_BROWSING:
       # Compute tcp configurations to apply on web server (with padding)
       tcp_configurations = list(itertools.product(ccs_web_browsing, ('cubic',), initcwnds))
    else:
       # Compute tcp configurations to apply on dash server (with padding)
       tcp_configurations = list(itertools.product(('cubic',), ccs_dash, initcwnds))

    return tcp_configurations

def print_tcp_conf(cc_web_browsing, cc_dash, initcwnd, traffic_type):
    if traffic_type is TrafficType.MIX:
       print('\t cc_web_browsing {0}, cc_dash {1} and initcwnd {2}'.format(cc_web_browsing, cc_dash, initcwnd))
       return
    if traffic_type is TrafficType.WEB_BROWSING:
       cc = cc_web_browsing
    else:
       cc = cc_dash
    print('\t cc {0}, and initcwnd {1}'.format(cc, initcwnd))
    
def get_traffic_infos(traffic_type, congestion):
    FILENAME = '/home/exploit/rt_adaptive_transport/extra_args_generate_{0}.txt'
    SCENARIO_NAME = 'Launch {0} service to compute {1}'

    if traffic_type is TrafficType.WEB_BROWSING:
       if congestion=='cubic':
          filename, scenario_name = (FILENAME.format('traffic_web_congestion'), 
                                     SCENARIO_NAME.format('background traffic cubic then web_browsing', 'PLT')) 
       elif congestion=='bbr2':
          filename, scenario_name = (FILENAME.format('traffic_web_congestion_bbr2'), 
                                     SCENARIO_NAME.format('background traffic bbr2 then web_browsing', 'PLT')) 
       else:
          filename, scenario_name = FILENAME.format('traffic_web'), SCENARIO_NAME.format('web_browsing', 'PLT') 

    if traffic_type is TrafficType.DASH:
       if congestion:
          filename, scenario_name = (FILENAME.format('traffic_dash_congestion'), 
                                     SCENARIO_NAME.format('background traffic then dash', 'bitrate'))
       else:
          filename, scenario_name = FILENAME.format('traffic_dash'), SCENARIO_NAME.format('dash', 'bitrate') 

    if traffic_type is TrafficType.MIX:
       if congestion:
          filename, scenario_name = (FILENAME.format('traffic_mix_congestion'), 
                                     SCENARIO_NAME.format('background traffic then web_browsing and dash', 'PLT and bitrate')) 
       else:
          filename, scenario_name = (FILENAME.format('traffic_mix'), 
                                     SCENARIO_NAME.format('web_browsing and dash', 'PLT and bitrate')) 

    return filename, scenario_name

def compute_legend(traffic_type, cc_web_browsing, cc_dash, initcwnd):
    legend = 'cc_{0} initcwnd_' + str(initcwnd)
    if traffic_type == TrafficType.MIX:
       return 'cc_web_{0} cc_dash_{1} initcwnd_{2}'.format(cc_web_browsing, cc_dash, initcwnd)
    elif traffic_type == TrafficType.WEB_BROWSING:
         return legend.format(cc_web_browsing)
    else:
         return legend.format(cc_dash)

def build(scenario_name, post_processing_entity, traffic_type, desired_test, losses=(0.0,), congestions=('None',), 
          ccs_web_browsing=('cubic',), ccs_dash=('cubic',), initcwnds=(10,)):
              
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format(traffic_type.value))   
    route = {'destination_ip':'192.168.19.0/24', 'gateway_ip':'192.168.42.1', 'initcwnd':'$initcwnd'}
    scenario_tcp_conf = transport_configuration_tcp_stack.build('$entity', '$cc', 'ens4', route)
    scenario_wifi_loss_apply = configure_link.build('$entity', '$ifaces', 'egress', 'apply', loss_model_params='$loss', scenario_name='apply_wifi_loss')
    scenario_wifi_loss_clear = configure_link.build('$entity', '$ifaces', 'egress', 'clear', scenario_name='clear_wifi_loss')
    if traffic_type is TrafficType.MIX: 
       entity_ifaces_list = [('client1', 'ens4'), ('client2', 'ens4'), ('ST', 'ens5')] 
    else: 
       entity_ifaces_list =  [('client1', 'ens4'), ('ST', 'ens5')]
    
    # Scenario for servers's rate monitoring
    match = {'interval':1, 'chain_name':'OUTPUT', 'destination_ip':'$destination_ip'}
    scenario_rate_monitoring = rate_monitoring.build('$entity', **match, scenario_name='rate_monitoring')
       
    network_conditions = list(itertools.product(losses, congestions))
    tcp_configurations = compute_tcp_confs(traffic_type, ccs_web_browsing, ccs_dash, initcwnds)
    
    wait_subscen_finished = None
    for loss, congestion in network_conditions:
        print('******** loss = {0} and congestion = {1} **********'.format(loss, congestion))
        subscenario = Scenario(SUBSCENARIO_NAME.format(traffic_type.value, loss, congestion), 
                               SUBSCENARIO_DESCRIPTION.format(traffic_type.value))      
        wait_finished, wait_launched, wait = [], [], []
        if loss:
           ### Add WIFI loss
           for entity, ifaces in entity_ifaces_list:
               start_wifi_loss = subscenario.add_function(                                                 
                     'start_scenario_instance')                                                             
               start_wifi_loss.configure(                                                               
                     scenario_wifi_loss_apply,
                     entity=entity,
                     ifaces=ifaces,
                     loss=loss)
               wait_finished.append(start_wifi_loss)
        else:
           ### Clear WIFI loss
           for entity, ifaces in entity_ifaces_list:
               start_wifi_loss = subscenario.add_function(                                                 
                     'start_scenario_instance')                                                             
               start_wifi_loss.configure(                                                               
                     scenario_wifi_loss_clear,
                     entity=entity,
                     ifaces=ifaces)
               wait_finished.append(start_wifi_loss)

        if congestion:
           ### TCP stack configuration for background traffic
           start_tcp_conf = subscenario.add_function(                                                 
                   'start_scenario_instance')                                                             
           start_tcp_conf.configure(                                                               
                   scenario_tcp_conf,
                   entity='serverB',
                   cc=congestion,
                   initcwnd=10)
           wait_finished.append(start_tcp_conf)   

        extra_args, test_name = get_traffic_infos(traffic_type, congestion)
        scenario_traffic = service_traffic_mix.build(None, extra_args, test_name)
        pp_scenario_traffic_infos = []
        pp_scenario_rate_monitoring_infos = defaultdict(list)
                 
        for cc_web_browsing, cc_dash, initcwnd in tcp_configurations:
            # Ignore not desired tests
            if not desired_test(traffic_type, loss, congestion, cc_web_browsing, cc_dash, initcwnd):
               continue  

            print_tcp_conf(cc_web_browsing, cc_dash, initcwnd, traffic_type)
            legend = compute_legend(traffic_type, cc_web_browsing, cc_dash, initcwnd)
            if congestion:
               ### Start rate monitoring on serverC
               start_rate_monitoring = subscenario.add_function(
                       'start_scenario_instance',
                       wait_finished=wait_finished)          
               start_rate_monitoring.configure(
                       scenario_rate_monitoring,
                       entity='serverB',
                       destination_ip='192.168.19.3')
               wait_launched.append(start_rate_monitoring)
               pp_scenario_rate_monitoring_infos['background server'].append((start_rate_monitoring, scenario_rate_monitoring, [legend]))

            if traffic_type in (TrafficType.WEB_BROWSING, TrafficType.MIX):
               ### Configure TCP Stack on apache2 server
               start_tcp_conf = subscenario.add_function(                                                 
                       'start_scenario_instance',
                       wait_finished=wait_finished)
               start_tcp_conf.configure(                                                               
                       scenario_tcp_conf,
                       entity='serverA',
                       cc=cc_web_browsing,
                       initcwnd=initcwnd)   
               wait.append(start_tcp_conf)
               ### Start rate monitoring
               start_rate_monitoring = subscenario.add_function(
                       'start_scenario_instance',
                       wait_finished=wait_finished)          
               start_rate_monitoring.configure(
                       scenario_rate_monitoring,
                       entity='serverA',
                       destination_ip='192.168.19.5')
               wait_launched.append(start_rate_monitoring)
               pp_scenario_rate_monitoring_infos['web server'].append((start_rate_monitoring, scenario_rate_monitoring, [legend]))
                 
            if traffic_type in (TrafficType.DASH, TrafficType.MIX):
               ### Configure TCP Stack on dash server
               start_tcp_conf = subscenario.add_function(                                                 
                       'start_scenario_instance',
                       wait_finished=wait_finished)
               start_tcp_conf.configure(                                                               
                       scenario_tcp_conf,
                       entity='serverB',
                       cc=cc_dash,
                       initcwnd=initcwnd)
               wait.append(start_tcp_conf)   
               ### Start rate monitoring
               start_rate_monitoring = subscenario.add_function(
                       'start_scenario_instance',
                       wait_finished=wait_finished)          
               start_rate_monitoring.configure(
                       scenario_rate_monitoring,
                       entity='serverB',
                       destination_ip='192.168.19.5')
               wait_launched.append(start_rate_monitoring)
               pp_scenario_rate_monitoring_infos['dash server'].append((start_rate_monitoring, scenario_rate_monitoring, [legend]))
                 
            ### Launch traffic
            start_scenario_traffic = subscenario.add_function(
                       'start_scenario_instance',
                       wait_finished=wait,
                       wait_launched=wait_launched,
                       wait_delay=5)
            start_scenario_traffic.configure(scenario_traffic)
            ### Stop rate monitoring 
            for start_rate_monitoring in wait_launched:
                stop_scenario_rate_monitoring = subscenario.add_function(
                         'stop_scenario_instance',
                          wait_finished=[start_scenario_traffic])
                stop_scenario_rate_monitoring.configure(
                          start_rate_monitoring)      
            wait_finished = wait_launched
            wait_launched = []
            ### Save infos for post processing
            legend = compute_legend(traffic_type, cc_web_browsing, cc_dash, initcwnd)
            pp_scenario_traffic_infos.append((start_scenario_traffic, scenario_traffic, [legend]))

        ### Post-Processing scenario traffic
        for job_name, stat_name, y_axis, title_ts, title_cdf in [
                ('web_browsing_qoe', 'page_load_time', 'PLT (ms)', 'Comparison of measured PLTs', 'CDF of PLT'),
                ('dash player&server', 'bitrate', 'Bitrate (b/s)', 'Comparison of measured Bitrates', 'CDF of Bitrate'),
	        ('iperf3', 'throughput', 'throughput (b/s)', 'Comparison of measured throughput (bg traffic)', 'CDF of Throughput (bg traffic)')]:
            post_processed, legends = [], []
            for start_scenario_traffic, scenario_traffic, legend in pp_scenario_traffic_infos:
                post_processed.extend(extract_jobs_to_postprocess_recursively(scenario_traffic, job_name, [start_scenario_traffic]))
                legends.append(legend)
            if post_processed:
               wait_finished = time_series_on_same_graph(subscenario, post_processing_entity, post_processed, [[stat_name]], [[y_axis]], [[title_ts]],
                                                         legends, wait_finished, None, 2) 
               wait_finished = cdf_on_same_graph(subscenario, post_processing_entity, post_processed, 100, [[stat_name]], [[y_axis]], [[title_cdf]],
                                                 legends, wait_finished, None, 2) 

        ### Post-processing scenarios rate-monitoring per server
        pp_scenario_rate_monitoring_infos = dict(pp_scenario_rate_monitoring_infos)
        for server, post_processing_infos in pp_scenario_rate_monitoring_infos.items():
            for job_name, stat_name, y_axis, title_ts, title_cdf in [
	            ('rate_monitoring', 'rate', 'bitrate (b/s)', 'Comparison of measured bitrate of {}'.format(server), 'CDF of bitrate of {}'.format(server)),
	            ('rate_monitoring', 'sent_data', 'sent data (bytes)', 'Comparison of measured sent data by {}'.format(server), 'CDF of sent data by {}'.format(server)),]:
                post_processed, legends = [], []
                for start_rate_monitoring, scenario_rate_monitoring, legend in post_processing_infos:
                    post_processed.extend(extract_jobs_to_postprocess_recursively(scenario_rate_monitoring, job_name, [start_rate_monitoring]))
                    legends.append(legend)
                if post_processed:
                   wait_finished = time_series_on_same_graph(subscenario, post_processing_entity, post_processed, [[stat_name]], [[y_axis]], [[title_ts]],
                                                         legends, wait_finished, None, 2) 
                   wait_finished = cdf_on_same_graph(subscenario, post_processing_entity, post_processed, 100, [[stat_name]], [[y_axis]], [[title_cdf]],
                                                 legends, wait_finished, None, 2) 
                                                     
        # Delay between test in order to empty OpenSAND queues
        wait_delay = 60 

        # Launch the subscenario from main scenario
        start_subscenario = scenario.add_function(
                'start_scenario_instance',
                 wait_finished=wait_subscen_finished
        )  
        start_subscenario.configure(
                subscenario,
        )
        wait_subscen_finished = [start_subscenario]
        
    return scenario
