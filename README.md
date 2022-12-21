OpenBACH
========

OpenBACH is a user-friendly and efficient benchmark to configure, supervise and
control your network under test (e.g. terrestrial networks, satellite networks,
WAN, LAN, etc.). It provides an efficient modular structure to facilitate the
additions of new software tools, monitoring parameters, tasks, etc. The
benchmark is able to be integrated in different types of equipments, servers,
clients, hardware and software with minimal adaptation effort.

This platform has been promoted by CNES (French Space Agency) as a reference
open-source software tool within its research and development studies and
activities in the domain of satellite network communications systems. OpenBACH
has been developped in order to be complementary to OpenSAND, the satellite
network emulator.

The documentation is scattered in this repository through README files at
appropriate places, a table of content is available below. This documentation
is also paired with the [main OpenBACH documentation][1].

OpenBACH EXTRA
==============

This repository contains extra elements for OpenBACH to extend, configure, or
interact with an OpenBACH platform:

 * All [API](/apis/README.md)s to use OpenBACH with CLI and develop python scripts:
    * [data access](/apis/data_access/README.md): to access data associated to the various scenario instances of an OpenBACH platform
    * [auditorium scripts](/apis/auditorium_scripts/README.md): to manage an OpenBACH platform
    * [scenario building scripts](/apis/scenario_builder/README.md) : to build scenarios programmatically and generate JSON files that can be imported into a project of an existing OpenBACH installation
      * [reference scenarios](/apis/scenario_builder/scenarios/README.md): basics scenario bricks to help build more complex scenarios
      * [helpers](/apis/scenario_builder/helpers/README.md): to simplify the scripting of your scenarios, by giving wrappers for common functions or tasks
 * All [extra jobs](/externals_jobs/README.md) not contained by default in OpenBACH.
 * All [executors](/executors/README.md) of [reference scenarios](/executors/references/README.md)
   and [examples](/executors/examples/README.md) maintained in OpenBACH to straightforward launch scenarios from CLI or import the JSON on existing OpenBACH platforms.
 * A tool to [test and validate](/validation_suite/README.md) an installed platform.

Cloning OpenBACH-extra on a machine can help manage multiple OpenBACH platforms. 
OpenBACH-extra can be exploited [to install, to set up and run tests using OpenBACH][2].

```
openbach-extra/
├── apis/
|   ├── data_access/
|   ├── auditorium_scripts/
|   └── scenario_builder/
|       ├── helpers/ -> predefined blocks of openbach functions that can be imported in scenarios.
|       └── scenarios/ -> reference scenarios to be imported in your scenarios.
├── external_jobs/ -> set of jobs that must be added to an OpenBACH controller 
|   |             for being used on a specific OpenBACH plateform
├── executors/ -> scripts ready to be launched from CLI: allow to run scenarios or
|   |             create scenario JSONs (to be imported in the OpenBACH web interface)
|   ├── reference/ -> executors maintained by the OpenBACH Team
|   └── examples/  -> other examples of executors
└── validation_suite/ -> automated script to test a platform and the auditorium scripts for regression
```

Set up OpenBACH EXTRA
=====================

The process that is required to set up the OpenBACH extra project is detailed in the [API](/apis/README.md) folder. 

Get Involved
============

  * See OpenBACH web site: http://www.openbach.org/
  * A mailing list is available: users@openbach.org

Project Partners
================

Vivéris Technologies

Authors
=======

  *  Adrien Thibaud      (Vivéris Technologies),      adrien.thibaud@viveris.fr
  *  Mathias Ettinger    (Vivéris Technologies),      mathias.ettinger@viveris.fr
  *  Joaquin Muguerza    (Vivéris Technologies),      joaquin.muguerza@viveris.fr
  *  Léa Thibout         (Vivéris Technologies),      lea.thibout@viveris.fr
  *  David Fernandes     (Vivéris Technologies),      david.fernandes@viveris.fr
  *  Bastien Tauran      (Vivéris Technologies),      bastien.tauran@viveris.fr
  *  Francklin Simo      (Vivéris Technologies),      francklin.simo@viveris.fr
  *  Mathieu Petrou      (Vivéris Technologies),      mathieu.petrou@viveris.fr
  *  Oumaima Zerrouq     (Vivéris Technologies),      oumaima.zerrouq@viveris.fr
  *  David Pradas        (Vivéris Technologies),      david.pradas@viveris.fr
  *  Emmanuel Dubois     (CNES),                      emmanuel.dubois@cnes.fr
  *  Nicolas Kuhn        (CNES),                      nicolas.kuhn@cnes.fr
  *  Santiago Garcia Guillen (CNES),                  santiago.garciaguillen@cnes.fr

Licence
=======

Copyright © 2016-2023 CNES
OpenBACH is released under GPLv3 (see [LICENSE](LICENSE.md) file).


[1]: https://github.com/CNES/openbach
[2]: https://github.com/NicoKos/openbach-example-4-agent
