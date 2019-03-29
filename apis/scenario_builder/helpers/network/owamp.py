def owamp_measure_owd(
        scenario, server_entity, client_entity, server_address,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'owamp-server', server_entity, offset=0,
            server_address=server_address)

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=5)
    client.configure(
            'owamp-client', client_entity, offset=0,
            destination_address=server_address)

    stopper = scenario.add_function(
            'stop_job_instance',
            wait_finished=[client])
    stopper.configure(server)

    return [server]


