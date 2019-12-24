#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016−2019 CNES
#
#
#   This file is part of the OpenBACH testbed.
#
#
#   OpenBACH is a free software : you can redistribute it and/or modify it under
#   the terms of the GNU General Public License as published by the Free Software
#   Foundation, either version 3 of the License, or (at your option) any later
#   version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
#   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
#   details.
#
#   You should have received a copy of the GNU General Public License along with
#   this program. If not, see http://www.gnu.org/licenses/.

""" Helpers of ftp_srv and ftp_clt jobs """

""" Make the client downloads a single file once, after that the server stops.
The path file needs to consider /srv/ as root """
def ftp_single_download(scenario, client_entity, server_entity, server_ip, port,
		file_path, user = None, password = None, blocksize = None):
	server = scenario.add_function('start_job_instance')
	server.configure('ftp_srv', server_entity, server_ip = server_ip, 
		port = port, user = user, password = password)

	client = scenario.add_function('start_job_instance',
		wait_launched = [server], wait_delay = 1)
	client.configure('ftp_clt', client_entity, server_ip = server_ip, 
		port = port, user = user, password = password, 	
		blocksize = blocksize, mode = 'download', 
		own = { 'file_path': file_path })

	stopper = scenario.add_function('stop_job_instance', 
		wait_finished=[client])
	stopper = configure(server)

	return [server]

""" Make the client uploads a single file once, after that the server stops.
The path file needs to consider /srv/ as the home directory """
def ftp_single_upload(scenario, client_entity, server_entity, server_ip, port,
		file_path, user = None, password = None, blocksize = None):
	server = scenario.add_function('start_job_instance')
	server.configure('ftp_srv', server_entity, server_ip = server_ip, 
		port = port, user = user, password = password)

	client = scenario.add_function('start_job_instance', 
		wait_launched = [server], wait_delay = 1)
	client.configure('ftp_clt', client_entity, server_ip = server_ip, 
		port = port, user = user, password = password,
		blocksize = blocksize, mode = 'upload',
		own = { 'file_path': file_path })

	stopper = scenario.add_function('stop_job_instance', 
		wait_finished=[client])
	stopper = configure(server)

	return [server]

""" Make the client downloads a single file multiple time every interval
during the predetermined duration, then it stops the client and the server. 
The path file needs to consider /srv/ as root """
def ftp_multiple_download(scenario, client_entity, server_entity, server_ip,
		port, duration, interval, file_path, user = None, 
		password = None, blocksize = None):
	server = scenario.add_function('start_job_instance')
	server.configure('ftp_srv', server_entity, server_ip = server_ip, 
		port = port, user = user, password = password)

	client = scenario.add_function('start_job_instance', 
		wait_launched = [server], wait_delay = 1)
	client.configure('ftp_clt', client_entity, Interval = interval,  
		server_ip = server_ip, port = port, user = user, 
		password = password, blocksize = blocksize, mode = 'download',
		own = { 'file_path': file_path })

	stop_clt = scenario.add_function('stop_job_instance', 
		wait_delay = duration, wait_launcher = [client])
	stop_clt.configure(client)

	stop_srv = scenario.add_function('stop_job_instance', 
		wait_finished=[stop_clt]) 
	stop_srv.configure(server)
	
	return [server]

""" Make the client uploads a single file multiple time every interval during 
the predetermined duration, then it stops the client and then the server.
The path file needs to consider /srv/ as the home directory  """
def ftp_multiple_download(scenario, client_entity, server_entity, server_ip, 
		port, duration, interval, file_path, user = None, 
		password = None, blocksize = None):
	server = scenario.add_function('start_job_instance')
	server.configure('ftp_srv', server_entity, server_ip = server_ip, 
		port = port, user = user, password = password)

	client = scenario.add_function('start_job_instance', 
		wait_launched = [server],wait_delay = 1)
	client.configure('ftp_clt', client_entity, Interval = interval,  
		server_ip = server_ip, port = port, user = user,
		password = password, blocksize = blocksize, mode = 'upload',
		own = { 'file_path': file_path })

	stop_clt = scenario.add_function('stop_job_instance', 
		wait_delay = duration, wait_launcher = [client])
	stop_clt.configure(client)

	stop_srv = scenario.add_function('stop_job_instance', 
		wait_finished=[stop_clt])
	stop_srv.configure(server)

	return [server]
