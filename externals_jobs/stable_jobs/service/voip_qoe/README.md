# openbach_jobs

Contact: Antoine Auger [antoine.auger@tesa.prd.fr](mailto:antoine.auger@tesa.prd.fr)

- Application service: Voice over IP (VoIP)
- Language: Python 3.5

## Jobs summary

Two complementary OpenBACH jobs have been developed in the context of this R&T:
- **voip_qoe_dest** is an OpenBACH job to measure the QoE of one or many VoIP sessions generated with D-ITG software. This job corresponds to the receiver (destination) component and should be launched before the caller (source) component.
- **voip_qoe_src** is an OpenBACH job to measure the QoE of one or many VoIP sessions generated with D-ITG software. This job corresponds to the caller (source) component and should be launched after the receiver (destination) component

## Requirements

- OpenBACH software (see [official website](http://www.openbach.org))
- 2 OpenBACH agents installed on two different hosts
- A password-less connection between the two hosts (see the "Installation instructions" for more details)

Both jobs have been extensively tested on Ubuntu 16.04 virtual machines with success. They may also work on other Ubuntu versions.

## Installation instructions

### /!\ IMPORTANT: Prerequisites 

You first want to setup a password-less ssh connection between your host 1 and your host 2, where *voip_qoe_src* and *voip_qoe_dest* jobs are installed, respectively.

This password-less connection should be enforced for both the OpenBACH user (generally openbach) and for the root user.

- __Step 1:__ key generation

On host 1 (*voip_qoe_src*), generate a pair of public keys using following command:

    ssh-keygen -t rsa

Then, press the [Enter] key three times to validate (default location, no password). The output should look like:

    Generating public/private rsa key pair.
    Enter file in which to save the key (/home/openbach/.ssh/id_rsa): [Press enter key]
    Created directory '/home/openbach/.ssh'.
    Enter passphrase (empty for no passphrase): [Press enter key]
    Enter same passphrase again: [Press enter key]
    Your identification has been saved in /home/openbach/.ssh/id_rsa.
    Your public key has been saved in /home/openbach/.ssh/id_rsa.pub.
    The key fingerprint is:
    5f:ad:40:00:8a:d1:9b:99:b3:b0:f8:08:99:c3:ed:d3 openbach@host1
    The key's randomart image is:
    +--[ RSA 2048]----+
    |        ..oooE.++|
    |         o. o.o  |
    |          ..   . |
    |         o  . . o|
    |        S .  . + |
    |       . .    . o|
    |      . o o    ..|
    |       + +       |
    |        +.       |
    +-----------------+ 

- __Step 2:__ key exchange

Copy the key from host 1 (*voip_qoe_src*) to host 2 (*voip_qoe_src*)

    ssh-copy-id openbach@host2
    
Then, test the password-less connection by typing `ssh openbach@host2`. You shoud not be prompted for any password.
    
- __Step 3__ 

On host 1, sudo as root:
    
    sudo su
    
- __Step 4__ 

Perform again step 1 and step 2.

Once -and only once- this has been done, the two jobs can be added to OpenBACH in three different ways.


### Option 1: Install on a fresh OpenBACH install

See the procedure described on OpenBACH wiki: [OpenBACH wiki - Adding Jobs from External Sources](https://wiki.net4sat.org/doku.php?id=openbach:manuals:installation_manual:index#adding_jobs_from_external_sources).

Typically, having installed the [ansible software](https://www.ansible.com/), the install command would be:

    ansible-playbook install.yml -u openbach -k -K -e '{"openbach_jobs_folders": ["/path/to/voip_qoe_src/", "/path/to/voip_qoe_dest/"]}'

Finally, remember to finalize Grafana association: [OpenBACH wiki - Manual Intervention](https://wiki.net4sat.org/doku.php?id=openbach:manuals:installation_manual:index#manual_intervention).

### Option 2: Install via OpenBACH GUI

- Go to the OpenBACH administration webpage at http://<CONTROLLER_IP>/app
- Click on the *OpenBACH* menu in the top-right corner and then on *Jobs*
- Enter *voip_qoe_src* in the *New Job Name* field
- Import the tar.gz archive containing the voip_qoe_src job 
- Repeat procedure for the voip_qoe_dest job

### Option 3: Install with auditorium scripts (CLI)

First, clone the Auditorium scripts repository from the forge

    git clone https://forge.net4sat.org/openbach/auditorium-scripts.git
    cd auditorium-scripts
    
Then, execute the `add_job.py` script with following arguments:

    ./add_job.py --controller <CONTROLLER_IP> --login openbach -p /path/to/voip_qoe_src/
    ./add_job.py --controller <CONTROLLER_IP> --login openbach -p /path/to/voip_qoe_dest/

or

    ./add_job.py --controller <CONTROLLER_IP> --login openbach -t /path/to/voip_qoe_src.tar.gz
    ./add_job.py --controller <CONTROLLER_IP> --login openbach -t /path/to/voip_qoe_dest.tar.gz

## Scenario example

We called *st* and *gw* the two agents that we used in our test_scenario.

This scenario is composed of three tasks:
- Task 1: start voip_qoe_dest (ITGRecv)
- Task 2: start voip_qoe_src (ITGSend)
- Task 3: stop voip_qoe_dest (ITGRecv)

JSON overview:

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

The scenario JSON file can also be found [here](https://forge.net4sat.org/tesa/rt16-tc8-29_partage-leo-geo/tree/master/openbach_jobs/test_scenario.json).
