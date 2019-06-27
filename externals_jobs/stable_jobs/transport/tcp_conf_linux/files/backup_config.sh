rm /etc/sysctl.d/60-openbach-tcp_conf_linux.conf
for param in tcp_congestion_control tcp_slow_start_after_idle tcp_no_metrics_save tcp_sack tcp_recovery tcp_wmem tcp_fastopen tcp_low_latency
do
    echo -n "net.ipv4." >> /etc/sysctl.d/60-openbach-tcp_conf_linux.conf
    echo -n $param >> /etc/sysctl.d/60-openbach-tcp_conf_linux.conf
    echo -n " = " >> /etc/sysctl.d/60-openbach-tcp_conf_linux.conf
	cat /proc/sys/net/ipv4/$param >> /etc/sysctl.d/60-openbach-tcp_conf_linux.conf
done
