#### Transport Rate & Traffic ####

def nuttcp_rate_udp(
        scenario, server_entity, client_entity, command_port,
        server_ip, port, receiver, duration, rate_limit,
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
                'receiver': receiver,
                'duration': duration,
                'rate_limit': rate_limit,
                'udp': {},
            })

    stopper = scenario.add_function(
            'stop_job_instance',
            wait_finished=[client])
    stopper.configure(server)

    return [server]

def iperf3_rate_tcp(
        scenario, server_entity, client_entity, 
        server_ip, port, receiver, duration, num_flows, tos, mtu,
        wait_finished=None, wait_launched=None, wait_delay=0):
    server = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    server.configure(
            'iperf3', server_entity, offset=0,
            port=port, num_flows=flow_count,
            interval=interval, server={'exit':True})

    client = scenario.add_function(
            'start_job_instance',
            wait_launched=[server],
            wait_delay=2)
    client.configure(
            'iperf3', client_entity, offset=0,
             num_flows=num_flows,
            client={
                'server_ip': server_ip,
                'port': port,
                'receiver': receiver,
                'duration_time': duration,
                'tos': '{0}'.format(tos),
                'tcp': {'mss':{}.format(mtu_40)},
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


#### Network Delay & Traffic ####

def fping_measure_rtt(
        scenario, client_entity, server_address, duration,
        wait_finished=None, wait_launched=None, wait_delay=0):
    ping = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    ping.configure(
            'fping', client_entity, offset=0,
            destination_ip=server_address)

    stop = scenario.add_function(
            'stop_job_instance',
            wait_launched=[ping],
            wait_delay=duration)
    stop.configure(ping)

    return [ping]


def hping_measure_rtt(
        scenario, client_entity, server_address, duration,
        wait_finished=None, wait_launched=None, wait_delay=0):
    ping = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    ping.configure(
            'hping', client_entity, offset=0,
            destination_ip=server_address)

    stop = scenario.add_function(
            'stop_job_instance',
            wait_launched=[ping],
            wait_delay=duration)
    stop.configure(ping)

    return [ping]
 

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


