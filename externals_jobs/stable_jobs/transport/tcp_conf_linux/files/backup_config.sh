rm /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf
for param in tcp_congestion_control tcp_slow_start_after_idle tcp_no_metrics_save tcp_sack tcp_recovery tcp_wmem tcp_fastopen tcp_low_latency
do
    echo -n "net.ipv4." >> /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf
    echo -n $param >> /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf
    echo -n "=" >> /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf
	cat /proc/sys/net/ipv4/$param >> /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf
done

rm /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf
for param in beta fast_convergence hystart_ack_delta hystart_low_window tcp_friendliness hystart hystart_detect initial_ssthresh 
do
    echo -n "net.ipv4." >> /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf
    echo -n $param >> /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf
    echo -n "=" >> /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf
	cat /sys/module/tcp_cubic/parameters/$param >> /opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf
done
