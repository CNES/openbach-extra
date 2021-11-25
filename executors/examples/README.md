Examples for exploiting OpenBACH
==================================================

This project constains examples that have been provided to detail how OpenBACH can be orchestrated using the reference scenarios.

<details><summary>example_opensand.py</summary>

This scenarios enables to configure the entities and run a full OpenSAND test.
It is based on the scenarios opensand_net_conf, opensand_satcom_conf and opensand_run.

#### Step-by-step description of the scenario :
    1. Parse the paths of the configuration files entered in the parameters
    2. Send those files to the OpenBACH Controller
    3. Launch opensand_net_conf to create and set the necessary bridges and TAP interfaces inside the ground entities (GWs and STs)
    4. Launch opensand_satcom_conf to push all the configuration files from the controller to each corresponding entity
    5. Launch opensand_run to run an OpenSAND test (start the entities and start the OpenSAND services)
    6. Launch opensand_net_conf to clean the network configuration 


#### Some words about the helper functions used in this example :
    - The function 'send_files_to_controller' is used to send the configuration files from the local machine to the controller (step 2)
    - The function '_extract_config_filepath' allows to get the configuration file inside the entity (step 5)


#### Parameters description :
  A detailed description of the parameters with examples is available in [OpenSAND documentation][1]
ollowing link:

  Note : if a configuration files is not set, the entity will load the one saved at :
  /etc/opensand/{infrastructure,topology,profile}.xml to run OpenSAND


#### Generated test reports:
    - The evolution of the the MODCOD used by the GW(s) and the ST(s)
    - The evolution of the throughput from the Satellite (kbps)
    - The CDF of the throughput from the Satellite (kbps)

</details>

<details><summary>data_transfer_configure_link.py</summary>
TBD
</details>

<details><summary>executor_tcp_evaluation_suite.py</summary>
TBD
</details>

<details><summary>executor_rate_monitoring.py</summary>
TBD
</details>

<details><summary>quic_configure_link.py</summary>
TBD
</details>

<details><summary>executor_reboot.py</summary>
TBD
</details>

[1]: https://github.com/CNES/opensand/

