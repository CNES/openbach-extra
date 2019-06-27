src = open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux.conf","r")
for line in src:
	name, value = line.split("=")
	while '.' in name:
		name = name.replace('.','/')
	dst=open("/proc/sys/"+name,"w")
	dst.write(value)
	dst.close()
src.close()

src = open("/opt/openbach/agent/jobs/tcp_conf_linux/default_tcp_conf_linux_cubic.conf","r")
for line in src:
	name, value = line.split("=")
	name = name.split('.')[-1]
	dst=open("/sys/module/tcp_cubic/parameters/"+name,"w")
	dst.write(value)
	dst.close()
src.close()