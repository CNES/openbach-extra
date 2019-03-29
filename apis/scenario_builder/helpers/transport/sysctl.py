def _sysctl_configure_tcp_congestion_control(
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


