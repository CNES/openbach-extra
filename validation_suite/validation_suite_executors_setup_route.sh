#!/usr/bin/bash
# -*- coding: utf-8 -*-
#
#   OpenBACH is a generic testbed able to control/configure multiple
#   network/physical entities (under test) and collect data from them. It is
#   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
#   Agents (one for each network entity that wants to be tested).
#
#
#   Copyright © 2016−2020 CNES
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

#################################################################################
#This script is part of the OpenBACH validation suite. 
#This script sets up the OpenBACH project using auditorium scripts. 
#The available entities are : 
#
#+------------+    +---------------+    +------------+    +-------------+
#|wss_admin_ip|    |midbox_admin_ip|    |wsc_admin_ip|    |ctrl_admin_ip|
#+------------+    +---------------+    +------------+    +-------------+
#|entity:     |    |entity:        |    |entity:     |    |             | 
#| wss        |    | midbox        |    |  wsc       |    |             |
#+------------+    +---------------+    +------------+    +-------------+
#|      wss_ip|    |midbox_ip_wss  |    |            |    |             |
#|      wss_if|    |midbox_if_wss  |    |            |    |             |
#|            |    |  midbox_ip_wsc|    |wsc_ip      |    |             |
#|            |    |  midbow_if_wsc|    |wsc_if      |    |             |
#+------------+    +---------------+    +------------+    +-------------+
#
#The different entity can be interconnected through the administration network
#This scenario sets up or remove the routes as follows 
#wss <-> midbox <-> wsc 
#
# Two options are available : 
#    add : to add all the necessary routes
#    delete : to delete all the routes that have been added with add option
#################################################################################

CHOICE=$1
wss_admin_ip=$2
wsc_admin_ip=$3
midbox_admin_ip=$4
wss_ip=$5
wss_if=$6   
midbox_ip_wss=$7   
midbox_if_wss=$8   
midbox_ip_wsc=$9   
midbox_if_wsc=${10}
wsc_ip=${11}
wsc_if=${12}

if [[ $CHOICE != "add" ]] && [[ $CHOICE != "delete" ]] 
then
        echo "Wrong entry" 
        echo "Enter the choice :"
	echo "add : to add all the necessary routes"
	echo "delete : to delete all the routes that have been added with add option"
        exit 1
fi

# wss -> midbox 
echo "--------------------------------------------------"
echo "Setting up wss -> midbox route"
echo "$wss_ip and $wss_if of $wss_admin_ip"
echo "routed to"
echo "$midbox_ip_wss and $midbox_if_wss of $midbox_admin_ip"

ssh -t $wss_admin_ip "JOB_NAME=ip_route sudo -E python3 /opt/openbach/agent/jobs/ip_route/ip_route.py $CHOICE -gw $wss_ip destination_ip $midbox_ip_wss"
echo "--------------------------------------------------"
echo " "

# midbox -> wsc 
echo "--------------------------------------------------"
echo "Setting up midbox -> wsc route"
echo "$midbox_ip_wsc and $midbox_if_wsc of $midbox_admin_ip"
echo "routed to"
echo "$wsc_ip and $wsc_if of $wsc_admin_ip"

ssh -t $midbox_admin_ip "JOB_NAME=ip_route sudo -E python3 /opt/openbach/agent/jobs/ip_route/ip_route.py $CHOICE -gw $midbox_ip_wsc destination_ip $wsc_ip"
echo "--------------------------------------------------"
echo " "

# midbox -> wss 
echo "--------------------------------------------------"
echo "Setting up midbox -> wss route"
echo "$midbox_ip_wss and $midbox_if_wss of $midbox_admin_ip"
echo "routed to"
echo "$wss_ip and $wss_if of $wss_admin_ip"

ssh -t $midbox_admin_ip "JOB_NAME=ip_route sudo -E python3 /opt/openbach/agent/jobs/ip_route/ip_route.py $CHOICE -gw $midbox_ip_wss destination_ip $wss_ip"
echo "--------------------------------------------------"
echo " "

# wsc -> midbox 
echo "--------------------------------------------------"
echo "Setting up wsc -> midbox route"
echo "$wsc_ip and $wsc_if of $wsc_admin_ip"
echo "routed to"
echo "$midbox_ip_wsc and $midbox_if_wsc of $midbox_admin_ip"

ssh -t $wsc_admin_ip "JOB_NAME=ip_route sudo -E python3 /opt/openbach/agent/jobs/ip_route/ip_route.py $CHOICE -gw $wsc_ip destination_ip $midbox_ip_wsc"
echo "--------------------------------------------------"
echo " "


