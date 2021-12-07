Scenario example
================

We called *st* and *gw* the two agents that we used in our test_scenario.

This scenario is composed of three tasks:

- Task 1: start voip_qoe_dest (ITGRecv)
- Task 2: start voip_qoe_src (ITGSend)
- Task 3: stop voip_qoe_dest (ITGRecv)

JSON overview:

.. code-block:: json

    {
      "name": "test_scenario",
      "constants": {},
      "openbach_functions": [
        {
          "label": "ITGRecv",
          "id": 131402243,
          "start_job_instance": {
            "offset": 0,
            "entity_name": "gw",
            "voip_qoe_dest": {}
          }
        },
        {
          "wait": {
            "launched_ids": [
              131402243
            ],
            "time": 3
          },
          "label": "ITGSend",
          "id": 194930622,
          "start_job_instance": {
            "offset": 0,
            "entity_name": "st",
            "voip_qoe_src": {
              "root_user_dest": "openbach",
              "nb_flows": "2",
              "src_addr": "192.168.10.78",
              "starting_port": "10002",
              "codec": "G.711.1",
              "duration": "10",
              "dest_addr": "192.168.10.195"
            }
          }
        },
        {
          "wait": {
            "finished_ids": [
              194930622
            ]
          },
          "label": "",
          "stop_job_instances": {
            "openbach_function_ids": [
              131402243
            ]
          },
          "id": 82989093
        }
      ],
      "description": "",
      "arguments": {}
    }

