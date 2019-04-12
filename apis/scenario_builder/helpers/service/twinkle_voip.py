def twinkle_voip(
       scenario, server_entity, local_ip, client_entity, remote_ip, duration,
       wait_finished=None, wait_launched=None, wait_delay=0):
    launch_server = scenario.add_function(
                       'start_job_instance',
                       wait_finished=wait_finished,
                       wait_launched=wait_launched,
                       wait_delay=wait_delay)
    launch_server.configure(
                     'twinkle_voip', server_entity, offset=0,
                     local_ip=local_ip, server=True)
    launch_client = scenario.add_function(
                       'start_job_instance',
                      wait_launched=[launch_server],
                      wait_delay=5)
    launch_client.configure(
                     'twinkle_voip', client_entity, offset=0,
                     local_ip=local_ip, remote_ip=remote_ip, length=duration)
    stop_server = scenario.add_function(
                     'stop_job_instance',
                     wait_finished=[launch_client])
    stop_server.configure(launch_server)

    return [launch_server]

