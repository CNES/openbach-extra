def web_browsing_qoe(                                                 
       scenario, entity, nb_runs, duration,               
       wait_finished=None, wait_launched=None, wait_delay=0):         
    launch_browsing = scenario.add_function(                          
                         'start_job_instance',                        
                         wait_finished=wait_finished,                 
                         wait_launched=wait_launched,                 
                         wait_delay=wait_delay)                       
    launch_browsing.configure(                                        
                       'web_browsing_qoe', entity, offset=0,   
                       nb_runs=nb_runs)       
    stop_launch_browsing = scenario.add_function(                     
                              'stop_job_instance',                    
                              wait_launched=[launch_browsing],        
                              wait_delay=duration)                    
    stop_launch_browsing.configure(launch_browsing)                   
                                                                      
    return [launch_browsing]                                          
