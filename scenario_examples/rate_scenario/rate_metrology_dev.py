#!/usr/bin/env python3

import itertools

import matplotlib.pyplot as plt
from scenario_observer import ScenarioObserver

import scenario_builder as sb


SCENARIO_NAME = 'New_Rate_Metrology'
SCENARIO_DESCRIPTION = 'Rate metrology scenario measuring network bandwidth'
UDP_RATES = range(10000, 17000, 4000)
NUTTCP_CLIENT_UDP_LABEL = 'nuttcp client: {} flows, rate {}, mtu {}b, tos {} (iter {})'
NUTTCP_SERVER_UDP_LABEL = 'nuttcp server: {} flows, rate {}, mtu {}b, tos {} (iter {})'
CLIENT_TCP_LABEL = '{} client: {} flows, mtu {}, tos {} (iter {})'
SERVER_TCP_LABEL = '{} server: {} flows, mtu {}, tos {} (iter {})'
PROJECT_NAME = 'rate_jobs'
POST_PROC = []

def build_rate_scenario(
        client_entity, server_entity, jobs=('iperf3', 'nuttcp', ),
        parallel_flows=(1, ), mtu_sizes=(1200,), tos_values=('0x00',),
        iterations=1, interval=1, udp=False):
    
    # Create the scenario with scenario_builder
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_DESCRIPTION)
    scenario.add_constant('dst_ip', '192.168.1.4') # The IP of the server
    scenario.add_constant('port', '7000') # The port of the server
    if 'nuttcp' in jobs:
        scenario.add_constant('com_port', '6000') # The port of nuttcp server for signalling
    scenario.add_constant('duration', '10') # The duration of each test (sec.)

    # Configure openbach functions and jobs
    wait_finished = []
    configurations = itertools.product(
            jobs, parallel_flows, mtu_sizes,
            tos_values, range(iterations))
    # The iteration creates different combinations per job and per parameter values (mtu size, number of parallel flows, ToS values.
    for job_name, flow_count, mtu, tos, iteration in configurations:
        if udp:
            if job_name == 'nuttcp':
                for rate in UDP_RATES:
                    launch_nuttcpserver = scenario.add_function(
                            'start_job_instance',
                            wait_finished=wait_finished,
                            label=NUTTCP_SERVER_UDP_LABEL.format(flow_count, rate, mtu, tos, iteration+1),
                    )
                    launch_nuttcpserver.configure(
                            job_name, server_entity, offset=0,
                            command_port='$com_port', server={}
                    )
                    launch_nuttcpclient = scenario.add_function(
                            'start_job_instance',
                            wait_launched=[launch_nuttcpserver],
                            wait_delay=2,
                            label=NUTTCP_CLIENT_UDP_LABEL.format(flow_count, rate, mtu, tos, iteration+1),
                    )
                    launch_nuttcpclient.configure(
                            job_name, client_entity, offset=0,
                            command_port='$com_port', client = {'server_ip':'$dst_ip',
                            'port':'$port', 'receiver':'{0}'.format(False), 'dscp':'{0}'.format(tos),
                            'stats_interval':'{0}'.format(interval), 'duration':'$duration',
                            'n_streams':'{0}'.format(flow_count), 'rate_limit':'{0}'.format(rate), 'udp':{}}
                    )
                    POST_PROC.append([NUTTCP_CLIENT_UDP_LABEL.format(flow_count, rate, mtu, tos, iteration+1), job_name, flow_count, iteration+1])
                    stop_nuttcpserver = scenario.add_function(
                         'stop_job_instance',
                         wait_finished=[launch_nuttcpclient],
                    )
                    stop_nuttcpserver.configure(launch_nuttcpserver)
                    wait_finished = [launch_nuttcpserver]
        else:
            if job_name == 'iperf3':
                    launch_iperf3server = scenario.add_function(
                        'start_job_instance',
                        wait_finished=wait_finished,
                        label=SERVER_TCP_LABEL.format(job_name, flow_count, mtu, tos, iteration+1),
                    )
                    launch_iperf3server.configure(
                         job_name, server_entity, offset=0, port='$port',
                         num_flows=flow_count,
                         interval=interval, server = {'exit':True}
                    )
                    POST_PROC.append([SERVER_TCP_LABEL.format(job_name, flow_count, mtu, tos, iteration+1), job_name, flow_count, iteration+1])
                    launch_iperf3client = scenario.add_function(
                        'start_job_instance',
                        wait_launched=[launch_iperf3server],
                        wait_delay=2,
                        label=CLIENT_TCP_LABEL.format(job_name, flow_count, mtu, tos, iteration+1),
                    )
                    launch_iperf3client.configure(
                        job_name, client_entity, offset=0,
                        port='$port', num_flows=flow_count, client = {'server_ip':'$dst_ip',
                        'duration':'$duration', 'tos':'{0}'.format(tos), 'tcp':{'mss':'{0}'.format(mtu-40)}}
                    )
                    wait_finished = [launch_iperf3client, launch_iperf3server]
            elif job_name == 'nuttcp':
                    launch_nuttcpserver = scenario.add_function(
                        'start_job_instance',
                        wait_finished=wait_finished,
                        label=SERVER_TCP_LABEL.format(job_name, flow_count, mtu, tos, iteration+1),
                    )
                    launch_nuttcpserver.configure(
                        job_name, server_entity, offset=0, 
                        command_port='$com_port', server={} 
                    )
                    launch_nuttcpclient = scenario.add_function(
                        'start_job_instance',
                        wait_launched=[launch_nuttcpserver],
                        wait_delay=2,
                        label=CLIENT_TCP_LABEL.format(job_name, flow_count, mtu, tos, iteration+1),
                    )
                    launch_nuttcpclient.configure(
                        job_name, client_entity, offset=0,
                        command_port='$com_port', client = {'server_ip':'$dst_ip',
                        'port':'$port', 'receiver':'{0}'.format(False), 'dscp':'{0}'.format(tos),
                        'stats_interval':'{0}'.format(interval), 'duration':'$duration', 
                        'n_streams':'{0}'.format(flow_count), 'tcp':{'mss':'{0}'.format(mtu-40)}}
                    )
                    POST_PROC.append([CLIENT_TCP_LABEL.format(job_name, flow_count, mtu, tos, iteration+1), job_name, flow_count, iteration+1])
                    stop_nuttcpserver = scenario.add_function(
                         'stop_job_instance',
                         wait_finished=[launch_nuttcpclient],
                    )
                    stop_nuttcpserver.configure(launch_nuttcpserver)
                    wait_finished = [launch_nuttcpserver]

    return scenario


def extract_iperf_statistic(job):
    data = job.statistics_data[('Flow1',)].dated_data
    return [
            (timestamp, stats['throughput'])
            for timestamp, stats in data.items()
    ]


def extract_iperf_statistics(job):
    data = job.statistics.dated_data
    return [
            (timestamp, stats['throughput'])
            for timestamp, stats in data.items()
    ]


def extract_nuttcp_statistics(job):
    data = job.statistics.dated_data
    return [
            (timestamp, stats['rate'])
            for timestamp, stats in data.items()
    ]


def main(project_name):
    #Build a scenario specifying the entity name of the client and the server.
    scenario_builder = build_rate_scenario('client', 'server', udp=False)
    scenario_builder.write('your_scenario.json')
    #ScenarioObserver creates the scenario / the post_processing is used to request the statistics from the desired jobs (by means of the labels of the openbach-functions)
    observer = ScenarioObserver(SCENARIO_NAME, project_name, scenario_builder)
    for pp in POST_PROC:
       if pp[1] == "iperf3":
           if pp[2] > 1:
               observer.post_processing(pp[0], extract_iperf_statistics, ignore_missing_label=True)
           else:
               observer.post_processing(pp[0], extract_iperf_statistic, ignore_missing_label=True)
       else:
           observer.post_processing(pp[0], extract_nuttcp_statistics, ignore_missing_label=True)

    # Launch and wait function starts your scenario, waits for the end and returns the results requested on post_processing.
    result = observer.launch_and_wait()
    
    # The plots: timeseries and CDF
    plt_thr = plt.figure(figsize=(12, 8), dpi=80, facecolor='w', edgecolor='k')
    plt.ylabel('Throughput (b/s)')
    plt.xlabel('Time (s)')
    plt.title('Comparison of Throughput')
    for label, values in result.items():
        origin = values[0][0]
        x = [v[0] - origin for v in values]
        y = [v[1] for v in values]
        plt.plot(x, y, label=label, markersize=15, linewidth=3)
    plt.legend()
    
    plt_cdf= plt.figure(figsize=(12, 8), dpi=80, facecolor='w', edgecolor='k')
    plt.ylabel('CDF')
    plt.xlabel('Throughput (b/s)')
    plt.title('CDF of Throughput test')
    for label, values in result.items():
        origin = values[0][0]
        x = [v[0] - origin for v in values]
        y = [v[1] for v in values]
        n, bins, patches = plt.hist(y, 1000, density=1, cumulative=True, label=label)
    plt.legend()

    plt_thr.show()
    plt_cdf.show()
    input()


if __name__ == '__main__':
    main('rate_jobs')
