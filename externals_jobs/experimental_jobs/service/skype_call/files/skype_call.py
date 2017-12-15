#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016 CNES
#
#
# This file is NOT part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.


""" Sources of the job skype_call """

__author__ = 'Thales Alenia Space'
__credits__ = ''' Contributors:
 * Romain Barbau <romain.barbau@free.fr>
'''


import argparse
import time
import collect_agent
import time
import os

import subprocess



def main(sim_t, Id):
	conffile = "/opt/openbach/agent/jobs/skype_call/skype_call_rstats_filter.conf"
	success = collect_agent.register_collect(conffile)

	if not success:
		return
	
	#Get the DISPLAY parameter on the agent.
	displayParameter = str(os.system("echo $DISPLAY"))
	#Launch Skype and then the call
	subprocess.call('xhost + ; export DISPLAY=:{0} ; python /opt/openbach/agent/jobs/skype_call/logInSkypeAndCall.py -t {1} -id {2}'.format(displayParameter, sim_t, Id) , shell = True)
	
	

if __name__ == "__main__":
	# Define Usage
	parser = argparse.ArgumentParser(description='', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-t','--sim_t', type=int, default=60, help='Time of the conversation in seconds. After that time the caller will end the call. Both will disconnect from Skype (Default = 60 sec).')
	parser.add_argument('-id','--id', type=int, default=1, help='The id of the skype pair. Knowing that we can\'t have 2 same id call instances on the same computer.Values can be 1,2,3 ... (Default = 1).')
	# get args
	args = parser.parse_args()
	sim_t = args.sim_t
	Id = args.id

	main(sim_t, Id)
