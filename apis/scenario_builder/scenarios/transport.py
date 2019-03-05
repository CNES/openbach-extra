from .. import Scenario
from ..helpers.traffic_and_metrics import iperf3_send_file_tcp
from ..helpers.configuration import multipath_tcp, terrestrial_link


def configure_mptcp(
        server, server_ifaces, server_terrestrial_iface, server_bandwidth,
        client, client_ifaces, client_terrestrial_iface, client_bandwidth,
        delay, scenario_name='Configure MpTCP'):
    scenario = Scenario(scenario_name, 'Configure MpTCP')

    wait = terrestrial_link(
            scenario, server, server_terrestrial_iface, server_bandwidth,
            client, client_terrestrial_iface, client_bandwidth, delay)
    multipath_tcp(scenario, server, server_ifaces, client, client_ifaces, wait)
    return scenario


def send_file_tcp(server, client, count=1, scenario_name='Measure Time'):
    scenario = Scenario(scenario_name, 'Measure time to transfer files using iperf3')
    scenario.add_argument('filesize', 'The size of the file to transfer')
    scenario.add_argument('dest_ip', 'The destination IP for the clients')
    scenario.add_argument('port', 'The port of the server')

    iperf3_send_file_tcp(scenario, server, client, '$filesize', '$dest_ip', '$port', count)
    return scenario
