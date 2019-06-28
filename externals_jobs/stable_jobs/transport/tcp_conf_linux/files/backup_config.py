dst = open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf","w")
for param in ["tcp_congestion_control", "tcp_slow_start_after_idle", 
		"tcp_no_metrics_save", "tcp_sack", "tcp_recovery", "tcp_wmem", "tcp_fastopen"]:
	src = open("/proc/sys/net/ipv4/"+param,"r")
	value = src.readline()
	src.close()
	dst.write("net.ipv4."+param+"="+value)
dst.close()

dst = open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf","w")
for param in ["beta", "fast_convergence", "hystart_ack_delta", "hystart_low_window",
		"tcp_friendliness", "hystart", "hystart_detect", "initial_ssthresh"]:
	src = open("/sys/module/tcp_cubic/parameters/"+param,"r")
	value = src.readline()
	src.close()
	dst.write(param+"="+value)
dst.close()