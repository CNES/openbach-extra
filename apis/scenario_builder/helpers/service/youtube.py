def youtube(
       scenario, entity, duration, wait_finished=None, wait_launched=None, wait_delay=0):
    launch_youtube = scenario.add_function(
                       'start_job_instance',
                       wait_finished=wait_finished,
                       wait_launched=wait_launched,
                       wait_delay=wait_delay)
    launch_youtube.configure(
                      'youtube', entity, offset=0,
                      duration=duration)
    
    return [launch_youtube]

