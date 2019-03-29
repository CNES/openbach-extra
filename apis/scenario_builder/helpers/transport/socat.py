def socat_send_files_tcp(
        scenario, server_entity, client_entity,
        filesize, destination_ip, port, clients_count,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'socat', server_entity, offset=0,
            server=True, port=port, file=filesize,
            create_file=True, measure_time=False)

    wait = []
    delay = 20  # Need big delay because file copy is slow
    for client_id in range(clients_count):
        client = scenario.add_function(
                'start_job_instance',
                wait_launched=[server],
                wait_finished=wait,
                wait_delay=delay)
        client.configure(
                'socat', client_entity, offset=2,
                server=False, dst_ip=destination_ip,
                port=port, file=filesize,
                create_file=False, measure_time=True)
        wait = [client]
        delay = 1

    stop = scenario.add_function(
            'stop_job_instance',
            wait_launched=[server],
            wait_finished=wait,
            wait_delay=delay)
    stop.configure(server)

    return [server]


