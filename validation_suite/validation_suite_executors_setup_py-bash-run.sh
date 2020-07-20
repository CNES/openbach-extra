#!/bin/bash

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

# Enter the choice : 
#   1- 'python' for test using python only
#   2- 'bash' for test using bash only
#   3- 'both' for test using bash and python

CHOICE=$1

if [[ $CHOICE != "bash" ]] && [[ $CHOICE != "python" ]] && [[ $CHOICE != "both" ]]
then 
	echo "Wrong entry" 
	echo "Enter the choice :"
	echo "'python' for test using python only"
	echo "'bash' for test using bash only"
	echo "'both' for test using bash and python"
	exit 1
fi

project=validsuite
wss=wss
wsc=wsc
midbox=midbox
wssIP=192.168.3.71
wscIP=192.168.3.69
midboxIP=192.168.3.70
# list the job installed by default to re-install them all
default_jobs=ip_route,fping,iperf3,rate_monitoring,rstats_job,rsyslog_job,send_logs,send_stats,synchronization
wssJ=$default_jobs,nuttcp,tcp_conf_linux
wscJ=$default_jobs,tcp_conf_linux
midboxJ=$default_jobs,tc_configure_link

if [[ $CHOICE = "python" ]] || [[ $CHOICE = "both" ]]
then
	echo "##################################################################"
	echo "Test PYTHON validation_suite_executors_setup.py"
	echo "##################################################################"
	echo " "
	python3 validation_suite_executors_setup.py -o $project --wss-entity $wss --wsc-entity $wsc --midbox-entity $midbox --wss-admin-ip $wssIP --wsc-admin-ip $wscIP --midbox-admin-ip $midboxIP --wss-jobs $wssJ --wsc-jobs $wscJ --midbox-jobs $midboxJ run
fi 

if [[ $CHOICE = "bash" ]] || [[ $CHOICE = "both" ]]
then
	echo "##################################################################"
	echo "Test BASH validation_suite_executors_setup.sh"
	echo "##################################################################"
	echo " "
	bash validation_suite_executors_setup.sh $project $wss $wsc $midbox $wssIP $wscIP $midboxIP $wssJ $wscJ $midboxJ
fi



