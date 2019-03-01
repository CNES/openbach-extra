from .. import Scenario
from ..helpers.traffic_and_metrics import owamp_measure_owd, fping_measure_rtt, hping_measure_rtt


def delay(client, server, scenario_name='Delay Metrology Scenario'):
    scenario = Scenario(scenario_name, 'Comparison of 3 RTT measurements')
    scenario.add_argument('ip_dst', 'Target of the pings and server ip adress')

    wait = owamp_measure_owd(scenario, server, client, '$ip_dst')
    hping = scenario.add_function('start_job_instance', wait_launched=wait)
    hping.configure('hping', client, offset=0, destination_ip='$ip_dst')
    fping = scenario.add_function('start_job_instance', wait_launched=wait)
    fping.configure('fping', client, offset=0, destination_ip='$ip_dst')

    stop = scenario.add_function('stop_job_instance', wait_finished=wait)
    stop.configure(hping, fping)

    return scenario


def delay_sequential(client, server, scenario_name='Delay Metrology Sequential Scenario'):
    scenario = Scenario(scenario_name, 'Comparison of RTT measurements sequentially')
    scenario.add_argument('ip_dst', 'Target of the pings and server ip adress')

    wait = fping_measure_rtt(scenario, client, '$ip_dst', 60)
    wait = hping_measure_rtt(scenario, client, '$ip_dst', 60, wait)
    wait = owamp_measure_owd(scenario, server, client, '$ip_dst', wait)

    return scenario
