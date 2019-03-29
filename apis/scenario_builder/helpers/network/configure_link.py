def _tc_configure_link_delay(
        scenario, delay, entity, interface,
        wait_finished=None, wait_launched=None, wait_delay=0):
    function = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    function.configure(
            'configure_link', entity,
            interface_name=interface, delay=delay)
    return function

def terrestrial_link(
        scenario, server, server_iface, server_bandwidth,
        client, client_iface, client_bandwidth, delay,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'configure_link', server, offset=0,
            bandwidth=server_bandwidth, delay=delay,
            interface_name=server_iface, loss=0.0)

    client = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    client.configure(
            'configure_link', client, offset=0,
            bandwidth=client_bandwidth, delay=delay,
            interface_name=client_iface, loss=0.0)

    return [client, server]
