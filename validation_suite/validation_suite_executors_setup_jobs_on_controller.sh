#!/bin/bash
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2019 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#  Author: Nicolas Kuhn / <nicolas.kuhn@cnes.fr>

# This script remove and add jobs to the controller
# requried parameters are: 
#  path_openbach : the path to the openbach/ repository
#  	e.g. /data/home/username/openbach/
#  path_openbach_extra : the path to the openbach-extra/ repository
#  	e.g. /data/home/username/openbach-extra/

if [ "$#" -ne 2 ]; then
	echo "Illegal number of parameters"
	echo "This script remove and add jobs to the controller"
	echo "requried parameters are:"
	echo "  path_openbach : the path to the openbach/ repository"
	echo "    e.g. /data/home/username/openbach/"
	echo "  path_openbach_extra : the path to the openbach-extra/ repository"
	echo "	  e.g. /data/home/username/openbach-extra/"
    exit 1
fi

path_openbach=$1 
path_openbach_extra=$2 

############################################################
############################################################
# openbach
############################################################
############################################################

# time_series
python3 ../apis/auditorium_scripts/delete_job.py time_series
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach/src/jobs/core_jobs/post_processing/time_series time_series

# histogram 
python3 ../apis/auditorium_scripts/delete_job.py histogram
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach/src/jobs/core_jobs/post_processing/histogram histogram

# tc_configure_link
python3 ../apis/auditorium_scripts/delete_job.py tc_configure_link
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach/src/jobs/core_jobs/network/tc_configure_link tc_configure_link

# ip_route
python3 ../apis/auditorium_scripts/delete_job.py ip_route
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach/src/jobs/core_jobs/network/ip_route ip_route

############################################################
############################################################
# openbach-extra
############################################################
############################################################

# owamp
python3 ../apis/auditorium_scripts/delete_job.py owamp-server
python3 ../apis/auditorium_scripts/delete_job.py owamp-client
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach_extra/externals_jobs/stable_jobs/network/owamp-client owamp-client
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach_extra/externals_jobs/stable_jobs/network/owamp-server owamp-server

# voip_qoe
python3 ../apis/auditorium_scripts/delete_job.py voip_qoe_dest
python3 ../apis/auditorium_scripts/delete_job.py voip_qoe_src
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach_extra/externals_jobs/stable_jobs/service/voip_qoe/voip_qoe_dest voip_qoe_dest
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach_extra/externals_jobs/stable_jobs/service/voip_qoe/voip_qoe_src voip_qoe_src

# nuttcp
python3 ../apis/auditorium_scripts/delete_job.py nuttcp
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach_extra/externals_jobs/stable_jobs/transport/nuttcp nuttcp

# tcp_conf_linux
python3 ../apis/auditorium_scripts/delete_job.py tcp_conf_linux
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach_extra/externals_jobs/stable_jobs/transport/tcp_conf_linux tcp_conf_linux

#d-itg
python3 ../apis/auditorium_scripts/delete_job.py d-itg_recv
python3 ../apis/auditorium_scripts/delete_job.py d-itg_send
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach_extra/externals_jobs/stable_jobs/network/d-itg_recv d-itg_recv
python3 ../apis/auditorium_scripts/add_job.py -f $path_openbach_extra/externals_jobs/stable_jobs/network/d-itg_send d-itg_send


