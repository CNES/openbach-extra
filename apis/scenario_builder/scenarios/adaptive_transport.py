from scenario_builder import Scenario
import scenario_builder.scenarios.transport_configuration_tcp_stack as transport_configuration_tcp_stack
import scenario_builder.scenarios.configure_link as configure_link
import scenario_builder.scenarios.service_traffic_mix as service_traffic_mix
from scenario_builder.helpers.postprocessing.time_series import time_series_on_same_graph
from scenario_builder.helpers.postprocessing.histogram import cdf_on_same_graph, pdf_on_same_graph
from scenario_builder.openbach_functions import StartJobInstance, StartScenarioInstance
import enum
import itertools


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
      BACKGROUNG='background'

def extract_jobs_to_postprocess(scenario, start_scenario_function, traffic):
    for subscenario_id, subscenario in enumerate(scenario.openbach_functions):
        if isinstance(subscenario, StartScenarioInstance) and isinstance(subscenario.scenario_name, Scenario):
            for function_id, function in enumerate(subscenario.scenario_name.openbach_functions):
                if isinstance(function, StartJobInstance):
                    if traffic is TrafficType.WEB_BROWSING and function.job_name == 'web_browsing_qoe':
                        yield [start_scenario_function, subscenario_id, function_id]
                    if traffic is TrafficType.DASH and function.job_name == 'dash player&server':
                        yield [start_scenario_function, subscenario_id, function_id]
                    elif traffic is TrafficType.BACKGROUNG and function.job_name == 'iperf3':
                        if 'server' in function.start_job_instance['iperf3']:
                            yield [start_scenario_function, subscenario_id, function_id]

def extract_jobs_to_postprocess_recursively(scenario, traffic, hierarchies=[]):
    for function_id, function in enumerate(scenario.openbach_functions):
        if isinstance(function, StartJobInstance):
           if traffic is TrafficType.WEB_BROWSING and function.job_name == 'web_browsing_qoe':
              yield hierarchies + [function_id]
           elif traffic is TrafficType.DASH and function.job_name == 'dash player&server':
              print('dash:' + str(hierarchies + [function_id]))
              yield hierarchies + [function_id]
           elif traffic is TrafficType.BACKGROUNG and function.job_name == 'iperf3':
                if 'server' in function.start_job_instance['iperf3']:
                   yield hierarchies + [function_id]
        elif isinstance(function, StartScenarioInstance) and isinstance(function.scenario_name, Scenario):
             yield from extract_jobs_to_postprocess_recursively(function.scenario_name, traffic, hierarchies + [function_id]) 

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
       if congestion:
          filename, scenario_name = (FILENAME.format('traffic_web_congestion'), 
                                     SCENARIO_NAME.format('background traffic then web_browsing', 'PLT')) 
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

def build(scenario_name, post_processing_entity, traffic_type, desired_test, losses=(0.0,), congestions=('None',), 
          ccs_web_browsing=('cubic',), ccs_dash=('cubic',), initcwnds=(10,)):
              
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION.format(traffic_type.value))   
    route = {'destination_ip':'192.168.19.0/24', 'gateway_ip':'192.168.42.1', 'initcwnd':'$initcwnd'}
    scenario_tcp_conf = transport_configuration_tcp_stack.build('$entity', '$cc', 'ens4', route)
    scenario_wifi_loss_apply = configure_link.build('$entity', '$ifaces', 'egress', 'apply', loss_model_params='$loss', scenario_name='apply_wifi_loss')
    scenario_wifi_loss_clear = configure_link.build('$entity', '$ifaces', 'egress', 'clear', scenario_name='clear_wifi_loss')
    if traffic_type == TrafficType.MIX.value: 
       entity_ifaces_list = [('client1', 'ens4'), ('client2', 'ens4'), ('ST', 'ens5')] 
    else: 
       entity_ifaces_list =  [('client1', 'ens4'), ('ST', 'ens5')]
       
    network_conditions = list(itertools.product(losses, congestions))
    tcp_configurations = compute_tcp_confs(traffic_type, ccs_web_browsing, ccs_dash, initcwnds)
    
    wait_subscen_finished = None
    for loss, congestion in network_conditions:
        print('******** loss = {0} and congestion = {1} **********'.format(loss, congestion))
        subscenario = Scenario(SUBSCENARIO_NAME.format(traffic_type.value, loss, congestion), 
                               SUBSCENARIO_DESCRIPTION.format(traffic_type.value))      
        wait_finished, wait = [], []
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
                   entity='serverC',
                   cc=congestion,
                   initcwnd=10)
           wait_finished.append(start_tcp_conf)   

        extra_args, test_name = get_traffic_infos(traffic_type, congestion)
        scenario_traffic = service_traffic_mix.build(None, extra_args, test_name)
        post_processing_infos = []
                 
        for cc_web_browsing, cc_dash, initcwnd in tcp_configurations:
            # Ignore not desired tests
            if not desired_test(traffic_type, loss, congestion, cc_web_browsing, cc_dash, initcwnd):
               continue  
            print_tcp_conf(cc_web_browsing, cc_dash, initcwnd, traffic_type)

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

            ### Launch traffic
            start_scenario_traffic = subscenario.add_function(
                       'start_scenario_instance',
                       wait_finished = wait)
            
            start_scenario_traffic.configure(scenario_traffic)
            wait_finished = [start_scenario_traffic]
            ### Save infos for post processing
            legend = 'cc_{0} initcwnd_' + str(initcwnd)
            post_processing_infos.append((start_scenario_traffic, scenario_traffic, [legend.format(cc_web_browsing)], [legend.format(cc_dash)]))
       
        ### Post-Processing
        for traffic, stat_name, y_axis, title_ts, title_cdf in [
                (TrafficType.WEB_BROWSING, 'page_load_time', 'PLT (ms)', 'Comparison of measured PLTs', 'CDF of PLT'),
                (TrafficType.DASH, 'bitrate', 'Bitrate (b/s)', 'Comparison of measured Bitrates', 'CDF of Bitrate'),]:
            post_processed, legends = [], []
            for start_scenario_traffic, scenario_traffic, legend_web_browsing, legend_dash in post_processing_infos:
                #post_processed.extend(extract_jobs_to_postprocess(scenario_traffic, start_scenario_traffic, traffic))
                post_processed.extend(extract_jobs_to_postprocess_recursively(scenario_traffic, traffic, [start_scenario_traffic]))
                legends.append(legend_web_browsing if traffic is TrafficType.WEB_BROWSING else legend_dash)
            print(post_processed)   
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
