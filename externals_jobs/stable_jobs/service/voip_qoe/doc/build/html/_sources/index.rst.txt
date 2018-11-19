.. OpenBACH jobs documentation master file, created by
   sphinx-quickstart on Mon Sep 10 11:53:55 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

*****************************
OpenBach jobs's documentation
*****************************

Two complementary OpenBACH jobs have been developed in the context of this R&T:

- **voip_qoe_dest** is an OpenBACH job to measure the QoE of one or many VoIP sessions generated with D-ITG software. This job corresponds to the receiver (destination) component and should be launched before the caller (source) component.
- **voip_qoe_src** is an OpenBACH job to measure the QoE of one or many VoIP sessions generated with D-ITG software. This job corresponds to the caller (source) component and should be launched after the receiver (destination) component

Contact: Antoine Auger [antoine.auger@tesa.prd.fr]

- Application service: Voice over IP (VoIP)
- Language: Python 3.5

Requirements
============

- OpenBACH software (see http://www.openbach.org)
- 2 OpenBACH agents installed on two different hosts
- A password-less connection between the two hosts (see the "Installation" section for more details)

Both jobs have been extensively tested on Ubuntu 16.04 virtual machines with success. They may also work on other Ubuntu versions.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   scenario_example
   voip_qoe_dest
   voip_qoe_src
