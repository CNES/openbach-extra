def _one_way_delay(
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


def _sysctl(
        scenario, entity, congestion_control,
        wait_finished=None, wait_launched=None, wait_delay=0):
    function = scenario.add_function(
            'start_job_instance',
            wait_finished=wait_finished,
            wait_launched=wait_launched,
            wait_delay=wait_delay)
    function.configure(
            'sysctl', entity,
            parameter='net.ipv4.tcp_congestion_control',
            value=congestion_control)
    return function


def configure_one_way_delays(
        scenario, delay, gateway_entity, gateway_interface,
        wait_finished=None, wait_launched=None, wait_delay=0, **work_stations):
    one_way_delays = [
            _one_way_delay(
                scenario, delay, entity, interface,
                wait_finished, wait_launched, wait_delay)
            for entity, (interface, _) in work_stations.items()
    ]
    one_way_delays.append(_one_way_delay(
        scenario, delay, gateway_entity, gateway_interface,
        wait_finished, wait_launched, wait_delay))

    return [
            _sysctl(scenario, entity, cc, one_way_delays)
            for entity, (_, cc) in work_stations.items()
    ]


def analyse_rate(
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


def analyse_one_way_delay(
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


def analyse_performances(
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


def analyse_rtt_fping(
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


def analyse_rtt_hping(
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
