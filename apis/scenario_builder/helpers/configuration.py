import enum


class WorkstationAction(enum.Enum):
    ADD = 1
    DELETE = 0


def multipath_tcp(
        scenario, server_entity, server_ifaces, client_entity, client_ifaces,
        wait_finished=None, wait_launched=None, wait_delay=0):

    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'mptcp', server_entity, offset=0,
            enable=True, path_manager='fullmesh',
            ifaces=','.join(server_ifaces))

    client = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    client.configure(
            'mptcp', client_entity, offset=0,
            enable=True, path_manager='fullmesh',
            ifaces=','.join(client_ifaces))

    return [client, server]


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
