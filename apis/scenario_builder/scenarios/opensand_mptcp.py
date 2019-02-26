from .. import Scenario
from ..scenarios.opensand import build_configure_scenario, build_emulation_scenario
from ..scenarios.transport import mptcp, configure_mptcp


FILE_SIZES = ('1M', '5M')


def build(
        topology, opensand_scenario,
        client, client_ifaces, client_terrestrial_iface, client_bandwidth,
        server, server_ifaces, server_terrestrial_iface, server_bandwidth,
        delay, count, destination_ip, port, scenario_name='MpTCP'):
    configure_opensand = build_configure_scenario(topology)
    opensand_emulation = build_emulation_scenario(topology)
    configure_mptcp_scenario = configure_mptcp(
            server, server_ifaces,
            server_terrestrial_iface,
            server_bandwidth,
            client, client_ifaces,
            client_terrestrial_iface,
            client_bandwidth, delay)
    mptcp_scenario = mptcp(server, client, count)

    scenario = Scenario(scenario_name, 'mptcp')
    start_configure_opensand = scenario.add_function('start_scenario_instance')
    start_configure_opensand.configure(configure_opensand)
    start_configure_mptcp = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_configure_opensand])
    start_configure_mptcp.configure(configure_mptcp_scenario)
    start_emulation = scenario.add_function(
            'start_scenario_instance',
            wait_finished=[start_configure_mptcp],
            wait_delay=10)
    start_emulation.configure(
            opensand_emulation,
            opensand_scenario=opensand_scenario)

    wait = []
    wait_delay = 30  # Give some time to OpenSAND to start
    for file_size in FILE_SIZES:
        start_mptcp = scenario.add_function(
                'start_scenario_instance',
                wait_launched=[start_emulation],
                wait_finished=wait,
                wait_delay=wait_delay)
        start_mptcp.configure(
                mptcp_scenario,
                filesize=file_size,
                dest_ip=destination_ip,
                port=str(port))
        wait = [start_mptcp]
        wait_delay = 1

    stop_opensand = scenario.add_function(
            'stop_scenario_instance',
            wait_launched=[start_emulation],
            wait_finished=wait,
            wait_delay=wait_delay)
    stop_opensand.configure(start_emulation)

    return scenario
