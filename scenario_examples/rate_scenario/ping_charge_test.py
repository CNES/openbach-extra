#!/usr/bin/env python3

import itertools

import matplotlib.pyplot as plt
from scenario_observer import ScenarioObserver

import scenario_builder as sb


SCENARIO_NAME = 'Performance_test'
SCENARIO_DESCRIPTION = 'Multiple pings to test web interface and openbach'
PING_LABEL = 'ping : number {}'
PROJECT_NAME = 'rate_jobs'
POST_PROC = []

def build_ping_scenario(
        client_entity, number_pings = 20, interval=0.5):
    
    # Create the scenario with scenario_builder
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_DESCRIPTION)
    scenario.add_constant('dst_ip', '192.168.1.4') # The IP of the server
    scenario.add_constant('duration', '10') # The duration of each test (sec.)

    # Configure openbach functions and jobs
    wait_finished = []
    # The iteration creates different combinations per job and per parameter values (mtu size, number of parallel flows, ToS values.
    for p in range(1,number_pings):
        launch_nuttcpserver = scenario.add_function(
                'start_job_instance',
                 wait_finished=wait_finished,
                 label=PING_LABEL.format(p),
        )
        launch_nuttcpserver.configure(
                 'fping', client_entity, offset=0, destinatio_ip='$dst_ip',
        )
    return scenario



def main(project_name):
    #Build a scenario specifying the entity name of the client and the server.
    scenario_builder = build_ping_scenario('client')
    scenario_builder.write('toto.json')
    #return
    #ScenarioObserver creates the scenario / the post_processing is used to request the statistics from the desired jobs (by means of the labels of the openbach-functions)
    observer = ScenarioObserver(SCENARIO_NAME, project_name, scenario_builder)

    # Launch and wait function starts your scenario, waits for the end and returns the results requested on post_processing.
    result = observer.launch_and_wait()
    
#    # The plots: timeseries and CDF
#    plt_thr = plt.figure(figsize=(12, 8), dpi=80, facecolor='w', edgecolor='k')
#    plt.ylabel('Throughput (b/s)')
#    plt.xlabel('Time (s)')
#    plt.title('Comparison of Throughput')
#    for label, values in result.items():
#        origin = values[0][0]
#        x = [v[0] - origin for v in values]
#        y = [v[1] for v in values]
#        plt.plot(x, y, label=label, markersize=15, linewidth=3)
#    plt.legend()
#    
#    plt_cdf= plt.figure(figsize=(12, 8), dpi=80, facecolor='w', edgecolor='k')
#    plt.ylabel('CDF')
#    plt.xlabel('Throughput (b/s)')
#    plt.title('CDF of Throughput test')
#    for label, values in result.items():
#        origin = values[0][0]
#        x = [v[0] - origin for v in values]
#        y = [v[1] for v in values]
#        n, bins, patches = plt.hist(y, 1000, density=1, cumulative=True, label=label)
#    plt.legend()
#
#    plt_thr.show()
#    plt_cdf.show()
#    input()



if __name__ == '__main__':
    main('rate_jobs')
