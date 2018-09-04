#!/usr/bin/env python3

import itertools

import matplotlib.pyplot as plt
from scenario_observer import ScenarioObserver

import scenario_builder as sb


SCENARIO_NAME = 'Rate_Metrology'
SCENARIO_DESCRIPTION = 'Rate metrology scenario measuring network bandwidth'
UDP_RATES = range(15_000_000, 17_000_000, 4_000_000)
NUTTCP_CLIENT_UDP_LABEL = 'nuttcp client {} flows {} rates ({})'
NUTTCP_SERVER_UDP_LABEL = 'nuttcp server {} flows {} rates ({})'
CLIENT_TCP_LABEL = '{} client {} flows ({})'
SERVER_TCP_LABEL = '{} server {} flows ({})'


def build_tcp_scenario(
        client_entity, server_entity, jobs=('iperf3', 'nuttcp'),
        parallel_flows=(1, 5), mtu_sizes=(1200,), tos_values=('0x00',),
        iterations=1, interval=0.5, udp=False):
    scenario = sb.Scenario(SCENARIO_NAME, SCENARIO_DESCRIPTION)
    scenario.add_constant('dst_ip', '192.168.1.4')
    scenario.add_constant('port', '7000')
    if 'nuttcp' in jobs:
        scenario.add_constant('com_port', '6000')
    scenario.add_constant('duration', '15')

    wait_finished = []
    configurations = itertools.product(
            jobs, parallel_flows, mtu_sizes,
            tos_values, range(iterations))
    for job_name, flow_count, mtu, tos, iteration in configurations:
        if udp:
            if job_name == 'nuttcp':
                for rate in UDP_RATES:
                    launch_nuttcpserver = scenario.add_function(
                            'start_job_instance',
                            wait_finished=wait_finished,
                            label=NUTTCP_SERVER_UDP_LABEL.format(flow_count, rate, iteration+1),
                    )
                    launch_nuttcpserver.configure(
                            job_name, server_entity, offset=0, port='$port',
                            server_mode=True, command_port='$com_port',
                    )
                    launch_nuttcpclient = scenario.add_function(
                            'start_job_instance',
                            wait_launched=[launch_nuttcpserver],
                            wait_delay=2,
                            label=NUTTCP_CLIENT_UDP_LABEL.format(flow_count, rate, iteration+1),
                    )
                    launch_nuttcpclient.configure(
                            job_name, client_entity, offset=0,
                            server_mode=False, server_ip='$dst_ip',
                            command_port='$com_port', port='$port', udp=True,
                            receiver=False, dscp='{0}'.format(tos), mss=mtu-40,
                            stats_interval=interval, rate_limit=rate,
                            duration='$duration', n_streams=flow_count,
                    )
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
                        label=SERVER_TCP_LABEL.format(job_name, flow_count, iteration+1),
                    )
                    launch_iperf3server.configure(
                         job_name, server_entity, offset=0, port='$port',
                         server_mode=True, num_flows=flow_count,
                         interval=interval, exit=True,
                    )
                    launch_iperf3client = scenario.add_function(
                        'start_job_instance',
                        wait_launched=[launch_iperf3server],
                        wait_delay=2,
                        label=CLIENT_TCP_LABEL.format(job_name, flow_count, iteration+1),
                    )
                    launch_iperf3client.configure(
                        job_name, client_entity, offset=0,
                        port='$port', server_mode=False,
                        client_mode_server_ip='$dst_ip',
                        time='$duration', num_flows=flow_count,
                        mss=mtu-40, tos=tos,
                    )
                    wait_finished = [launch_iperf3client, launch_iperf3server]
            elif job_name == 'nuttcp':
                    launch_nuttcpserver = scenario.add_function(
                        'start_job_instance',
                        wait_finished=wait_finished,
                        label=SERVER_TCP_LABEL.format(job_name, flow_count, iteration+1),
                    )
                    launch_nuttcpserver.configure(
                        job_name, server_entity, offset=0, port='$port',
                        server_mode=True, command_port='$com_port',
                    )
                    launch_nuttcpclient = scenario.add_function(
                        'start_job_instance',
                        wait_launched=[launch_nuttcpserver],
                        wait_delay=2,
                        label=CLIENT_TCP_LABEL.format(job_name, flow_count, iteration+1),
                    )
                    launch_nuttcpclient.configure(
                        job_name, client_entity, offset=0,
                        server_mode=False, server_ip='$dst_ip',
                        command_port='$com_port', port='$port',
                        receiver=False, dscp='{0}'.format(tos),
                        mss=mtu-40, stats_interval=interval,
                        duration='$duration', n_streams=flow_count,
                    )
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
    scenario_builder = build_tcp_scenario('client', 'server', udp=False)
    observer = ScenarioObserver(SCENARIO_NAME, project_name, scenario_builder)
    observer.post_processing('iperf3 server 1 flows (1)', extract_iperf_statistic, ignore_missing_label=True)
    observer.post_processing('nuttcp client 1 flows (1)', extract_nuttcp_statistics, ignore_missing_label=True)
    observer.post_processing('iperf3 server 5 flows (1)', extract_iperf_statistics, ignore_missing_label=True)
    observer.post_processing('nuttcp client 5 flows (1)', extract_nuttcp_statistics, ignore_missing_label=True)
    result = observer.launch_and_wait()

    plt.figure(figsize=(12, 8), dpi=80, facecolor='w', edgecolor='k')
    plt.ylabel('Throughput (b/s)')
    plt.xlabel('Time (s)')
    plt.title('Comparison of throughput')
    for label, values in result.items():
        origin = values[0][0]
        x = [v[0] - origin for v in values]
        y = [v[1] for v in values]
        plt.plot(x, y, label=label, markersize=15, linewidth=3)
    plt.legend()
    plt.show()


if __name__ == '__main__':
    main('rate_jobs')
