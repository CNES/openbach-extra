#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright � 2018 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.


"""Sources of the Job smtp"""

__author__ = 'Viveris Technologies'
__credits__ = '''Contributors:
 * Francklin SIMO <francklin.simo@toulouse.viveris.com>
'''

import sys
import math
import time
import syslog
import smtplib
import asyncio
import argparse
import email.utils
from random import choices
from string import ascii_uppercase
from email.mime.text import MIMEText

from aiosmtpd.controller import Controller

import collect_agent


SENDER = {'name' : 'Sender', 'email':'sender@mail.dummy.com'}
RECEIVER = {'name' : 'Receiver', 'email':'receiver@mail.dummy.com'}
SUBJECT = 'Background traffic'
DEFAULT_PORT = 1025


class Handler:
    def __init__(self):
        self.nb_messages = 0
        self.data_received = 0

    async def handle_DATA(self, server, session, enveloppe):
        data = enveloppe.content
        self.nb_messages += 1
        self.data_received += (len(enveloppe.content) + sys.getsizeof('')) // 1024
        collect_agent.send_stat(collect_agent.now(), received_messages=self.nb_messages, received_data_size=self.data_received)
        return '250 OK'


def handle_exception(exception):
    message = 'ERROR: {}'.format(exception)
    collect_agent.send_log(syslog.LOG_ERR, message)
    return message


def server(server_port):
    server = Controller(Handler(), hostname='0.0.0.0', port=server_port)
    server.start()
    collect_agent.wait_for_signal()
    server.stop()


def generate_string(size):
    '''Generate a random string of the specified size in kilobytes'''
    # Break string into 1000 char lines, see RFC5321 4.5.3.1.6
    string_length = size * 1024 
    lines, footer_length = divmod(string_length, 1000)
    body = '\n'.join(''.join(choices(ascii_uppercase, k=999)) for _ in range(lines))
    footer = ''.join(choices(ascii_uppercase, k=footer_length))
    if body:
        return body + '\n' + footer
    return footer


def client(server_ip, server_port, sender, receiver, message_size, interval, duration):
    # Create the message
    message = generate_string(message_size)
    msg = MIMEText(message)
    msg['To'] = email.utils.formataddr((receiver['name'], receiver['email']))
    msg['From'] = email.utils.formataddr((sender['name'], sender['email']))
    msg['Subject'] = SUBJECT
    try:
        server = smtplib.SMTP(server_ip, server_port)
        # Show communication with the server
        server.set_debuglevel(True) 
    except ConnectionRefusedError as ex:
        message = handle_exception(ex)
        sys.exit(message)
    # Send message
    ref = int(time.time())
    try:
        while (time.time() - ref) < duration:
            server.sendmail(sender['email'], receiver['email'], msg.as_string())
            time.sleep(interval)
    except Exception as ex:
        message = handle_exception(ex)
        sys.exit(message)
    finally:
        server.quit()


if __name__ == "__main__":
    with collect_agent.use_configuration('/opt/openbach/agent/jobs/smtp/smtp_rstats_filter.conf'):
        # Define usage
        parser = argparse.ArgumentParser(description='',
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
                '-s', '--server_mode', action='store_true',
                help='Run in server mode')
        group.add_argument(
                '-c', '--server_ip', type=str,
                help='Run in client mode and specify server IP address')
        parser.add_argument(
                '-p', '--server_port', type=int, default=DEFAULT_PORT,
                help='Set server port to listen on/connect to')      
        parser.add_argument(
                '-F', '--From', type=str, default=SENDER['email'],
                help='The sender email address (client only)')
        parser.add_argument(
                '-T', '--To', type=str, default=RECEIVER['email'],
                help='The receiver email address (client only)')
        parser.add_argument(
                '-S', '--size', type=int, default=100,
                help='The size in kilobyte of the message to send (client only)')
        parser.add_argument(
                '-i', '--interval', type=float, default=1,
                help='The pause *interval* seconds between messages to send'
                '(client only)')
        parser.add_argument(
                '-d', '--duration', type=int, default=math.inf,
                help='The time in seconds to send messages (client only)')
            
        # Parse arguments
        args = parser.parse_args()
        server_port = args.server_port
        if args.server_mode:
            server(server_port)
        else:
            server_ip = args.server_ip
            sender = {'name':args.From.split("@")[0], 'email':args.From}
            receiver = {'name':args.To.split("@")[0], 'email':args.To}
            message_size = args.size
            interval = args.interval
            duration = args.duration
            client(server_ip, server_port, sender, receiver, message_size, interval, duration)
