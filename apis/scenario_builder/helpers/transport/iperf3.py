def iperf3_rate_tcp(
        scenario, server_entity, client_entity, 
        server_ip, port, duration, num_flows, tos, mtu,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'iperf3', server_entity, offset=0,
            num_flows=num_flows, port=port,
            interval=1.0, server={'exit':True})

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', client_entity, offset=0,
             num_flows=num_flows, port=port,
             client={
                'server_ip': server_ip,
                'duration_time': duration,
                'tos': '{0}'.format(tos),
                'tcp': {'mss':'{0}'.format(mtu)},
            })

    stopper = scenario.add_function(
            'stop_job_instance',
            wait_finished=[client])
    stopper.configure(server)

    return [server]


def iperf3_send_file_tcp(
        scenario, server_entity, client_entity,
        port, server_ip, transmitted_size,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'iperf3', server_entity, offset=0,
            port=port, server={'exit': True})

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', client_entity, offset=0,
            port=port, client={
                'server_ip': server_ip,
                'transmitted_size': transmitted_size,
                'tcp': {},
            })

    return [server]


