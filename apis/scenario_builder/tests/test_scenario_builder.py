#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2023 CNES
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

__author__ = 'Mathias ETTINGER <mathias.ettinger@toulouse.viveris.com>'
__version__ = 'v0.3'


import unittest

import scenario_builder as sb


class TestScenarioBuilder(unittest.TestCase):
    def test_condition_creation(self):
        expected_results = {
            'type': 'and',
            'left_condition': {
                'type': '<',
                'left_operand': {
                    'type': 'value',
                    'value': '3',
                },
                'right_operand': {
                    'type': 'value',
                    'value': '5',
                },
            },
            'right_condition': {
                'type': '>',
                'left_operand': {
                    'type': 'value',
                    'value': '4',
                },
                'right_operand': {
                    'type': 'value',
                    'value': '6',
                },
            },
        }

        cond = sb.Condition('and',
                sb.Condition('<',
                    sb.Operand('value', '3'),
                    sb.Operand('value', '5')),
                sb.Condition('>',
                    sb.Operand('value', '4'),
                    sb.Operand('value', '6')))

        self.assertEqual(cond.build([]), expected_results)

    def test_scenario_if(self):
        expected_results = {
            "name": "If",
            "description": "If scenario (for test)",
            "arguments": {},
            "constants": {
                "agentA": "172.20.34.38",
                "agentB": "172.20.34.37",
                "agentC": "172.20.34.39"
            },
            "openbach_functions": [
                {
                    "id": 0,
                    "label": "#0",
                    "reboot": {
                        "entity_name": "Agent A",
                        "kernel": "default",
                    },
                    "wait": {
                        "time": 0,
                        "launched_ids": [],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 1,
                    "label": "#1",
                    "if": {
                        "condition": {
                            "type": "=",
                            "left_operand": {
                                "type": "database",
                                "name": "Agent",
                                "key": "$agentA",
                                "attribute": "status"
                            },
                            "right_operand": {
                                "type": "value",
                                "value": "available"
                            }
                        },
                        "openbach_functions_true": [2, 3],
                        "openbach_functions_false": [4]
                    },
                    "wait": {
                        "time": 0,
                        "launched_ids": [0],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 2,
                    "label": "#2",
                    "start_job_instance": {
                        "entity_name": "Agent A",
                        "fping": {
                            "destination_ip": "$agentB",
                            "duration": 60
                        },
                        "offset": 5
                    },
                    "wait": {
                        "time": 0,
                        "launched_ids": [],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 3,
                    "label": "#3",
                    "start_job_instance": {
                        "entity_name": "Agent B",
                        "fping": {
                            "destination_ip": "$agentA",
                            "duration": 60
                        },
                        "offset": 5
                    },
                    "wait": {
                        "time": 0,
                        "launched_ids": [],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 4,
                    "label": "#4",
                    "start_job_instance": {
                        "entity_name": "Agent B",
                        "fping": {
                            "destination_ip": "$agentC",
                            "duration": 60
                        },
                        "offset": 5
                    },
                    "wait": {
                        "time": 0,
                        "launched_ids": [],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 5,
                    "label": "#5",
                    "stop_job_instances": {
                        "openbach_function_ids": [2, 3]
                    },
                    "wait": {
                        "time": 10,
                        "launched_ids": [2, 3],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 6,
                    "label": "#6",
                    "stop_job_instances": {
                        "openbach_function_ids": [4]
                    },
                    "wait": {
                        "time": 10,
                        "launched_ids": [4],
                        "finished_ids": []
                    },
                    "on_fail": {},
                }
            ]
        }

        scenario = sb.Scenario('If', 'If scenario (for test)')
        scenario.add_constant('agentA', '172.20.34.38')
        scenario.add_constant('agentB', '172.20.34.37')
        scenario.add_constant('agentC', '172.20.34.39')
        reboot = scenario.add_function('reboot')
        reboot.configure('Agent A', kernel='default')
        if_function = scenario.add_function('if', wait_launched=[reboot])
        if_function.configure(
                sb.Condition('=',
                sb.Operand('database', 'Agent', '$agentA', 'status'),
                sb.Operand('value', 'available')))
        ping_a_b = scenario.add_function('start_job_instance')
        ping_a_b.configure('fping', 'Agent A', offset=5, destination_ip='$agentB', duration=60)
        ping_b_a = scenario.add_function('start_job_instance')
        ping_b_a.configure('fping', 'Agent B', offset=5, destination_ip='$agentA', duration=60)
        ping_b_c = scenario.add_function('start_job_instance')
        ping_b_c.configure('fping', 'Agent B', offset=5, destination_ip='$agentC', duration=60)
        if_function.configure_if_true(ping_a_b, ping_b_a)
        if_function.configure_if_false(ping_b_c)
        scenario.add_function('stop_job_instance', 10, [ping_a_b, ping_b_a]).configure(ping_a_b, ping_b_a)
        scenario.add_function('stop_job_instance', 10, [ping_b_c]).configure(ping_b_c)

        self.assertEqual(scenario.build(), expected_results)

    def test_scenario_while(self):
        expected_results = {
            "name": "While",
            "description": "While scenario (for test)",
            "arguments": {},
            "constants": {
                "agentA": "172.20.34.38",
                "agentB": "172.20.34.37",
                "agentC": "172.20.34.39"
            },
            "openbach_functions": [
                {
                    "id": 0,
                    "label": "#0",
                    "reboot": {
                        "entity_name": "Agent A",
                        "kernel": "default",
                    },
                    "wait": {
                        "time": 0,
                        "launched_ids": [],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 1,
                    "label": "#1",
                    "while": {
                        "condition": {
                            "type": "=",
                            "left_operand": {
                                "type": "database",
                                "name": "Agent",
                                "key": "$agentA",
                                "attribute": "status"
                            },
                            "right_operand": {
                                "type": "value",
                                "value": "Available"
                            }
                        },
                        "openbach_functions_while": [2],
                        "openbach_functions_end": [3]
                    },
                    "wait": {
                        "time": 0,
                        "launched_ids": [0],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 2,
                    "label": "#2",
                    "reboot": {
                        "entity_name": "Agent B",
                        "kernel": "default",
                    },
                    "wait": {
                        "time": 0,
                        "launched_ids": [],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 3,
                    "label": "#3",
                    "start_job_instance": {
                        "entity_name": "Agent B",
                        "fping": {
                            "destination_ip": "$agentC",
                            "duration": 60
                        },
                        "offset": 5
                    },
                    "wait": {
                        "time": 0,
                        "launched_ids": [],
                        "finished_ids": []
                    },
                    "on_fail": {},
                },
                {
                    "id": 4,
                    "label": "#4",
                    "stop_job_instances": {
                        "openbach_function_ids": [3]
                    },
                    "wait": {
                        "time": 10,
                        "launched_ids": [3],
                        "finished_ids": []
                    },
                    "on_fail": {},
                }
            ]
        }

        scenario = sb.Scenario('While', 'While scenario (for test)')
        scenario.add_constant('agentA', '172.20.34.38')
        scenario.add_constant('agentB', '172.20.34.37')
        scenario.add_constant('agentC', '172.20.34.39')
        reboot = scenario.add_function('reboot')
        reboot.configure('Agent A', kernel='default')
        while_function = scenario.add_function('while', wait_launched=[reboot])
        while_function.configure(
                sb.Condition('=',
                sb.Operand('database', 'Agent', '$agentA', 'status'),
                sb.Operand('value', 'Available')))
        reboot = scenario.add_function('reboot')
        reboot.configure('Agent B', kernel='default')
        ping = scenario.add_function('start_job_instance')
        ping.configure('fping', 'Agent B', offset=5, destination_ip='$agentC', duration=60)
        while_function.configure_while_body(reboot)
        while_function.configure_while_end(ping)
        scenario.add_function('stop_job_instance', 10, [ping]).configure(ping)

        self.assertEqual(scenario.build(), expected_results)


if __name__ == '__main__':
    unittest.main()
