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
 


