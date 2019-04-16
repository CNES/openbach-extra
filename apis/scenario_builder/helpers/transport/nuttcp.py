def nuttcp_rate_udp(
        scenario, server_entity, client_entity,
        server_ip, port, command_port, duration, rate_limit,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'nuttcp', server_entity, offset=0,
            command_port=command_port, server={})

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'nuttcp', client_entity, offset=0,
            command_port=command_port,
            client={
                'server_ip': server_ip,
                'port': port,
                'duration': duration,
                'rate_limit': rate_limit,
                'udp': {},
            })

    stopper = scenario.add_function(
            'stop_job_instance',
            wait_finished=[client])
    stopper.configure(server)

    return [server]

def nuttcp_rate_tcp(
        scenario, server_entity, client_entity,
        server_ip, port, command_port, duration, num_flows, tos, mtu,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'nuttcp', server_entity, offset=0,
            command_port=command_port, server={})

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'nuttcp', client_entity, offset=0,
            command_port=command_port, 
            client={
                'server_ip': server_ip,
                'port': port,
                'dscp':'{0}'.format(tos),
                'n_streams': num_flows, 
                'receiver': format(False),
                'duration': duration,
                'tcp': {'mss':'{0}'.format(mtu)},
            })

    stopper = scenario.add_function(
            'stop_job_instance',
            wait_finished=[client])
    stopper.configure(server)

    return [server]



