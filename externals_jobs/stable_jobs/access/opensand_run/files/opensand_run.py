#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
   OpenBACH is a generic testbed able to control/configure multiple
   network/physical entities (under test) and collect data from them. It is
   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
   Agents (one for each network entity that wants to be tested).
   
   
   Copyright © 2019 CNES
   
   
   This file is part of the OpenBACH testbed.
   
   
   OpenBACH is a free software : you can redistribute it and/or modify it under the
   terms of the GNU General Public License as published by the Free Software
   Foundation, either version 3 of the License, or (at your option) any later
   version.
   
   This program is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
   details.
   
   You should have received a copy of the GNU General Public License along with
   this program. If not, see http://www.gnu.org/licenses/.
   
   
   
   @file     opensand_run.py
   @brief    Sources of the Job opensand-emulation
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
   @author   Joaquin MUGUERZA <joaquin.muguerza@toulouse.viveris.com>
   @author   Aurelien DELRIEU <adelrieu@toulouse.viveris.com>
"""

import os
import sys
import time
import signal
import syslog
import os.path
import argparse
from functools import partial

sys.path.append('/usr/lib/python3/dist-packages/')
from opensand_manager_shell.opensand_shell_manager import ShellManager, \
        BaseFrontend, \
        ShellMgrException
from opensand_manager_core.loggers.levels import MGR_WARNING, LOG_LEVELS


# Temporary fix
os.environ["HOME"] = "/home/openbach/"


class OpsError(Exception):
    ''' OpenSAND error '''

    def __init__(self, message):
        '''
        Initialize openSAND error.
        '''
        super(OpsError, self).__init__(self, message)


class OpsLogger(object):
    ''' OpenSAND logger '''

    def __init__(self, verbose=False):
        '''
        Initialize the OpenSAND logger.
        '''
        self._prefix = "[OpenSAND Emulation]"
        self._verbose = verbose

    def log(self, priority, message):
        '''
        Send a log message with priority.

        Args:
            priority:  the log priority for syslog
            message:   the log message
        '''
        if self._verbose:
            prefix = '[ERROR] ' if priority == syslog.LOG_ERR else ''
            print(prefix + message)

    def info(self, message):
        '''
        Send an info message.
        
        Args:
            message:  the info message
        '''
        self.log(syslog.LOG_INFO, message)

    def err(self, message):
        '''
        Send an error message.
        
        Args:
            message:  the error message
        '''
        self.log(syslog.LOG_ERR, message)


class OpsEmulation(object):
    ''' OpenSAND Emulation '''
    def __init__(self, verbose=False, platform_id=None):
        '''
        Initialize emulation with arguments.

        Args:
            logger:       the log sender
            platform_id:  the platform identifier (can be None).
        '''
        self._logger = OpsLogger(verbose)

        self._service_type = \
                self._get_ops_service_type(platform_id)

        self._manager = ShellManager()
        self._frontend = BaseFrontend()
        
        self._opened = False
        self._started = False
        
        self._logger.info('Platform id set to "{}"'.format(platform_id))
        self._logger.info('OpenSAND service type set to "{}"'.format(self._service_type))

    def _get_ops_service_type(self, platform_id):
        '''
        Get the OpenSAND service type.

        Args:
            platform_id:  the string identifying the OpenSAND platform.

        Returns:
            the OpenSAND service type.
        '''
        if platform_id is None or platform_id == '':
            return '_opensand._tcp'
        return '_{}_opensand._tcp'.format(platform_id)

    def is_running(self):
        '''
        Get the running status.

        Returns:
            true if running, false otherwise.
        '''
        return self._opened and self._started

    def open(self):
        '''
        Open the emulation detecting hosts of the platform.

        Raises:
            OpsError:  if opening failed
        
        Remarks:
            This method can be blocking in case of excpetion raising.
            Indeed, the load method of the OpenSAND shell manager launches
            some thread.
        '''
        # Check opened status
        if self._opened:
            self._logger.info('Hosts already detected')
            return
        self._started = False

        # Load manager
        try:
            self._logger.info('Detecting hosts...')
            self._manager.load(log_level = MGR_WARNING,
                               service = self._service_type,
                               with_ws = True,
                               remote_logs = False,
                               frontend = self._frontend)
            self._logger.info('Hosts detected')
            self._opened = True
        except KeyboardInterrupt as err:
            self._logger.info('Hosts detection interrupted: {}'.format(err))
            self._logger.info('Releasing emulation...')
            self._manager.close()
            self._logger.info('Emulation released')
            raise err
        except ShellMgrException as err:
            # Main host not found => emulation is not startable
            self._manager.close()
            self._logger.err('Hosts detection failed: {}'.format(err))
            raise OpsError('Hosts detection failed: {}'.format(err))

    def close(self):
        '''
        Close the emulation releasing hosts of the platform.
        '''
        # Check opened status
        if not self._opened:
            self._logger.info('Emulation already released')
            return

        # Close manager
        self._logger.info('Releasing emulation...')
        self._manager.close()
        self._logger.info('Emulation released')
        self._opened = False

    def start(self, scenario_path=None):
        '''
        Start emulation.

        Args:
            scenario_path:  the directory path to the OpenSAND scenario.

        Raises:
            OpsError:  if scenario settings failed or
                       if platform starting failed.
        '''
        # Check started status
        if self._started:
            self._logger.info('OpenSAND platform already started')
            return

        # Configure scenario
        try:
            self._logger.info('Deploying emulation scenario'
                             ' "{}"...'.format('default'
                                               if scenario_path is None
                                               else scenario_path))
            if scenario_path is not None:
                self._manager.set_scenario(scenario_path)
            self._logger.info('Emulation scenario'
                             ' "{}" deployed'.format('default'
                                                     if scenario_path is None
                                                     else scenario_path))
        except ShellMgrException as err:
            self._logger.err('Emulation scenario deployment failed: {}'.format(err))
            raise OpsError('Emulation scenario deployment failed: {}'.format(err))

        # Start platform
        try:
            self._logger.info('Starting OpenSAND platform...')
            self._manager.start_opensand()
            self._logger.info('OpenSAND platform started')
            self._started = True
        except ShellMgrException as err:
            self._logger.err('OpenSAND platform starting failed: {}'.format(err))
            raise OpsError('OpenSAND platform starting failed: {}'.format(err))


    def stop(self):
        '''
        Stop emulation.

        Raises:
            OpsError:  if platform stopping failed.
        '''
        retries = 3
        is_running = partial(str.__eq__, 'running')
        # Stop platform
        self._logger.info('Stopping OpenSAND platform...')
        while any(map(is_running, self._manager.status_opensand().values())) and retries:
            try:
                self._manager.stop_opensand()
            except ShellMgrException as err:
                self._logger.err('OpenSAND platform stopping failed: {}'.format(err))
                raise OpsError('OpenSAND platform stopping failed: {}'.format(err))
            retries -= 1
        if retries == 0:
            self._logger.err('OpenSAND platform stopping failed: {}'.format(err))
            return
        self._logger.info('OpenSAND platform stopped')
        self._started = False

    def __enter__(self):
        '''
        Open emulation.
        '''
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        '''
        Close emulation.
        '''
        self.close()


def ops_scen_path(value):
    '''
    Define OpenSAND scenario path.
    Check value is matching or not.
    
    Args:
        value:  the value to check.
    
    Returns:
        the matching value.
    
    Raises:
        ArgumentTypeError:  if value is not an existing directory path or 
                            if it does match the OpenSAND scenario template.
    '''
    # Check default value
    if value is None:
        return value

    # Check it is an existing directory
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError('Directory \"{}\" does not '
                                         'exist'.format(value))
    
    # Check the directory matches the OpenSAND scenario template
    required_paths = ['topology.conf', 'core_global.conf', 'modcod']
    if not all(os.path.exists(os.path.join(value, path))
               for path in required_paths):
        raise argparse.ArgumentTypeError('Directory \"{}\" does not '
                                         'match OpenSAND scenario'
                                         'template'.format(value))

    return value   

def no_operation_handler(signal, frame):
    '''
    No operation when signal is catched.
    '''
    pass

if __name__ == "__main__":
    # Define Usage
    parser = argparse.ArgumentParser(description='',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Global optional arguments
    parser.add_argument('--platform-id', type=str,
                        help='The plateform id (default is none)')
    parser.add_argument('--scenario-path', type=ops_scen_path,
                        help='The local path of the OpenSAND scenario '
                        '(default is none)')
    parser.add_argument('--force-stop', action='store_true',
                        help='Force the stop of the emulation'
                        '(no emulation starting')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Set verbose output')

    # Check and get args
    args = parser.parse_args()

    # Initialize emulation
    with OpsEmulation(args.verbose, args.platform_id) as emu:
        # Force initial stop
        try:
            emu.stop()
        except OpsError as err:
            if args.force_stop:
                raise err

        # Exit if stop is forced
        if args.force_stop:
            sys.exit(0)

        # Start emulation
        try:
            emu.start(args.scenario_path)
        except OpsError as err:
            # Starting failed => force stop
            try:
                emu.stop()
            except OpsError:
                pass
            raise err

        # Wait interruption
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, no_operation_handler)
        signal.pause()

        # Stop emulation
        emu.stop()
