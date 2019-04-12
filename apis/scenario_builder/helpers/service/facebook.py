def facebook(
       scenario, receiver_entity, receiver_email_address, receiver_password,  
       caller_entity, caller_email_address, caller_password, receiver_contact, call_type,
       duration, timeout, wait_finished=None, wait_launched=None, wait_delay=0):
    receive = scenario.add_function(
                'start_job_instance',
                wait_finished=wait_finished,
                wait_launched=wait_launched,
                wait_delay=wait_delay)
    receive.configure(
                'facebook', receiver_entity, offset=0,
                email_address=receiver_email_address,
                password=receiver_password,
                call_type=call_type,
                timeout=timeout,
                receiver={})
    
    call = scenario.add_function(
            'start_job_instance', 
            wait_launched=[receive],
            wait_delay=5)
    call.configure(
            'facebook', caller_entity, offset=0,
            email_address=caller_email_address,
            password=caller_password,
            call_type=call_type,
            timeout=timeout,
            caller={'friend_name':receiver_contact,
                    'call_duration':duration})
    stop = scenario.add_function(
            'stop_job_instance',
            wait_finished=[call]
           )
    stop.configure(receive)

    return [receive]  
 
