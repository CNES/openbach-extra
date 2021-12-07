Installation instructions
=========================

IMPORTANT: Prerequisites
~~~~~~~~~~~~~~~~~~~~~~~~

You first want to setup a password-less ssh connection between your host 1 and your host 2, where *voip_qoe_src* and *voip_qoe_dest* jobs are installed, respectively.

This password-less connection should be enforced for both the OpenBACH user (generally openbach) and for the root user.

- Step 1: key generation

On host 1 (*voip_qoe_src*), generate a pair of public keys using following command:

.. code-block:: console

    ssh-keygen -t rsa

Then, press the [Enter] key three times to validate (default location, no password). The output should look like:

.. code-block:: console

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

- Step 2: key exchange

Copy the key from host 1 (*voip_qoe_src*) to host 2 (*voip_qoe_src*)

.. code-block:: console

    ssh-copy-id openbach@host2

Then, test the password-less connection by typing:

.. code-block:: console

    ssh openbach@host2

You shoud not be prompted for any password.

- Step 3

On host 1, sudo as root:

.. code-block:: console

    sudo su

- Step 4

Perform again step 1 and step 2.

Once -and only once- this has been done, the two jobs can be added to OpenBACH in three different ways.

Option 1: Install on a fresh OpenBACH install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the procedure described on OpenBACH wiki:

- OpenBACH wiki: Adding Jobs from External Sources https://github.com/CNES/openbach-extra/blob/dev/externals_jobs/README.md

Typically, having installed the [ansible software](https://www.ansible.com/), the install command would be:

.. code-block:: console

    ansible-playbook install.yml -u openbach -k -K -e '{"openbach_jobs_folders": ["/path/to/voip_qoe_src/", "/path/to/voip_qoe_dest/"]}'

Option 2: Install via OpenBACH GUI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Go to the OpenBACH administration webpage at http://<CONTROLLER_IP>/app
- Click on the *OpenBACH* menu in the top-right corner and then on *Jobs*
- Enter *voip_qoe_src* in the *New Job Name* field
- Import the tar.gz archive containing the voip_qoe_src job
- Repeat procedure for the voip_qoe_dest job

Option 3: Install with auditorium scripts (CLI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, clone the Auditorium scripts repository from the forge

.. code-block:: console

    git clone https://github.com/CNES/openbach-extra
    cd openbach-extra/apis/auditorium_scripts

Then, execute the `add_job.py` script with following arguments:

.. code-block:: console

    ./add_job.py --controller <CONTROLLER_IP> --login openbach -p /path/to/voip_qoe_src/
    ./add_job.py --controller <CONTROLLER_IP> --login openbach -p /path/to/voip_qoe_dest/

or

.. code-block:: console

    ./add_job.py --controller <CONTROLLER_IP> --login openbach -t /path/to/voip_qoe_src.tar.gz
    ./add_job.py --controller <CONTROLLER_IP> --login openbach -t /path/to/voip_qoe_dest.tar.gz
