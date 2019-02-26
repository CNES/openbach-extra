from .. import Scenario
from ..helpers.metrics import analyse_one_way_delay, analyse_rtt_fping, analyse_rtt_hping


def delay(client, server, scenario_name='Delay Metrology Scenario'):
    scenario = Scenario(scenario_name, 'Comparison of 3 RTTs')
    scenario.add_argument('ip_dst', 'Target of the pings and server ip adress')

    wait = analyse_one_way_delay(scenario, server, client, '$ip_dst')
    hping = scenario.add_function('start_job_instance', wait_launched=wait)
    hping.configure('hping', client, offset=0, destination_ip='$ip_dst')
    fping = scenario.add_function('start_job_instance', wait_launched=wait)
    fping.configure('fping', client, offset=0, destination_ip='$ip_dst')

    stop = scenario.add_function('stop_job_instance', wait_finished=wait)
    stop.configure(hping, fping)

    return scenario


def delay_sequential(client, server, scenario_name='Delay Metrology Scenario'):
    scenario = Scenario(scenario_name, 'Comparison of 3 RTTs at different times')
    scenario.add_argument('ip_dst', 'Target of the pings and server ip adress')

    wait = analyse_rtt_hping(scenario, client, '$ip_dst', 60)
    wait = analyse_rtt_fping(scenario, client, '$ip_dst', 60, wait)
    wait = analyse_one_way_delay(scenario, server, client, '$ip_dst', wait)

    return scenario
