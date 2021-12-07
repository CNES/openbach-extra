# openbach_jobs

Contact: Antoine Auger [antoine.auger@tesa.prd.fr](mailto:antoine.auger@tesa.prd.fr)
         Bastien Tauran [bastien.tauran@toulouse.viveris.com](mailto:bastien.tauran@toulouse.viveris.com)

- Application service: Voice over IP (VoIP)
- Language: Python 3.5

## Jobs summary

Two complementary OpenBACH jobs have been developed in the context of this R&T:
- **voip_qoe_dest** is an OpenBACH job to measure the QoE of one or many VoIP sessions generated with D-ITG software. This job corresponds to the receiver (destination) component and should be launched before the caller (source) component.
- **voip_qoe_src** is an OpenBACH job to measure the QoE of one or many VoIP sessions generated with D-ITG software. This job corresponds to the caller (source) component and should be launched after the receiver (destination) component

## Requirements

- OpenBACH software (see [official website](http://www.openbach.org))
- 2 OpenBACH agents installed on two different hosts
- Both hosts must have a common ntp time synchronisation

Both jobs have been extensively tested on Ubuntu 16.04 virtual machines with success. They may also work on other Ubuntu versions.

## Installation instructions

### Option 1: Install on a fresh OpenBACH install

See the procedure described on OpenBACH manual: [Adding Jobs from External Sources](https://github.com/CNES/openbach-extra/blob/dev/externals_jobs/README.md).

Typically, having installed the [ansible software](https://www.ansible.com/), the install command would be:

    ansible-playbook install.yml -u openbach -k -K -e '{"openbach_jobs_folders": ["/path/to/voip_qoe_src/", "/path/to/voip_qoe_dest/"]}'

### Option 2: Install via OpenBACH GUI

- Go to the OpenBACH administration webpage at http://<CONTROLLER_IP>/app
- Click on the *OpenBACH* menu in the top-right corner and then on *Jobs*
- On the left colum, under *Install a supported external job*, click on *Voip Qoe Src* and install it
- Repeat procedure for the *Voip Qoe Dest* job

### Option 3: Install with auditorium scripts (CLI)

First, clone the Auditorium scripts repository from the forge

    git clone https://github.com/CNES/openbach-extra
    cd openbach-extra/apis/auditorium_scripts
    
Then, execute the `add_job.py` script with following arguments:

    ./add_job.py --controller <CONTROLLER_IP> --login openbach -p /path/to/voip_qoe_src/
    ./add_job.py --controller <CONTROLLER_IP> --login openbach -p /path/to/voip_qoe_dest/

or

    ./add_job.py --controller <CONTROLLER_IP> --login openbach -t /path/to/voip_qoe_src.tar.gz
    ./add_job.py --controller <CONTROLLER_IP> --login openbach -t /path/to/voip_qoe_dest.tar.gz

## Scenario example

We called *agent_src* and *agent_dst* the two agents that we used in our test_scenario.

This scenario is composed of three tasks:
- Task 1: start voip_qoe_dest (ITGRecv)
- Task 2: start voip_qoe_src (ITGSend)
- Task 3: stop voip_qoe_dest (ITGRecv)

JSON overview:

    {
      "name": "test_scenario_voip",
      "constants": {},
      "openbach_functions": [
        {
          "label": "ITGRecv",
          "id": 131402243,
          "start_job_instance": {
            "offset": 0,
            "entity_name": "agent_dst",
            "voip_qoe_dest": {
              "dest_addr": "192.168.1.2"
            }
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
            "entity_name": "agent_src",
            "voip_qoe_src": {
              "nb_flows": "2",
              "src_addr": "192.168.1.1",
              "starting_port": "10002",
              "codec": "G.711.1",
              "duration": "30",
              "dest_addr": "192.168.1.2"
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
