def mtcp_multipath(
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



