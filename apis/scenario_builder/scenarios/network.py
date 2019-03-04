from .. import Scenario
from ..helpers.traffic_and_metrics import owamp_measure_owd, fping_measure_rtt, hping_measure_rtt

def delay_simultaneous(client, server, scenario_name='Delay Metrology Simultaneous Scenario'):
    scenario = Scenario(scenario_name, 'Comparison of three RTT measurements simultaneously')
    scenario.add_argument('ip_dst', 'Target of the pings and server ip adress')

    owamp_measure_owd(scenario, server, client, '$ip_dst')
    fping_measure_rtt(scenario, client, '$ip_dst', 60)
    hping_measure_rtt(scenario, client, '$ip_dst', 60)

    return scenario


def delay_sequential(client, server, scenario_name='Delay Metrology Sequential Scenario'):
    scenario = Scenario(scenario_name, 'Comparison of three RTT measurements sequentially')
    scenario.add_argument('ip_dst', 'Target of the pings and server ip adress')

    wait = fping_measure_rtt(scenario, client, '$ip_dst', 60)
    wait = hping_measure_rtt(scenario, client, '$ip_dst', 60, wait)
    wait = owamp_measure_owd(scenario, server, client, '$ip_dst', wait)

    return scenario
