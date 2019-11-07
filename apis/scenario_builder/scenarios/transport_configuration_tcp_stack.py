from scenario_builder import Scenario
from scenario_builder.helpers.transport.tcp_conf_linux import tcp_conf_linux_repetitive_tests
from scenario_builder.helpers.transport.ethtool import ethtool_disable_segmentation_offload
from scenario_builder.helpers.network.ip_route import ip_route



SCENARIO_DESCRIPTION=""""""
SCENARIO_NAME="""transport_configuration_tcp_stack"""


def configure_tcp_stack(scenario, entity, dev, route):
    tcp_conf_linux_repetitive_tests(scenario, entity, '$cc')
    if dev:
       ethtool_disable_segmentation_offload(scenario, entity, dev)
    if route:
       ip_route(scenario, entity, 'change', **route, initcwnd='$initcwnd')
    
    return scenario   


def tcp_stack_configuration(server, dev=None, route=None):
    scenario = Scenario('TCP stack configuration on {0}'.format(server), 'Configure TCP stack')
    scenario.add_argument('cc', 'The congestion control to apply')
    if route:
       scenario.add_argument('initcwnd', 'The initial congestion window to appy')
    configure_tcp_stack(scenario, server, dev, route)

    return scenario

def build(server, interface, cc, initcwnd, scenario_name=SCENARIO_NAME):
    route = {'destination_ip':'192.168.0.0/24', 'gateway_ip':'192.168.0.42'}
     # Create scenario and subscenario core
    scenario = Scenario(scenario_name, SCENARIO_DESCRIPTION)
    start_tcp_conf = scenario.add_function(
            'start_scenario_instance')
    scenario_tcp_conf = tcp_stack_configuration(server, interface, route) 
    start_tcp_conf.configure(
            scenario_tcp_conf,
            cc=cc,
            initcwnd=initcwnd)

    return scenario
