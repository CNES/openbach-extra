def netflix(
       scenario, entity, email_address, password, duration, timeout,
       wait_finished=None, wait_launched=None, wait_delay=0):
    launch_netflix = scenario.add_function(
                       'start_job_instance',
                       wait_finished=wait_finished,
                       wait_launched=wait_launched,
                       wait_delay=wait_delay)
    launch_netflix.configure(
                      'netflix', entity, offset=0, 
                       email_address=email_address, 
                       password=password, 
                       duration=duration, timeout=timeout)
   
    return [launch_netflix]

