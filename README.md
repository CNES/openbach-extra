OpenBACH
========

OpenBACH is a user-friendly and efficient benchmark to configure, supervise and
control your network under test (e.g. terrestrial networks, satellite networks,
WAN, LAN, etc.). It provides an efficient modular structure to facilitate the
additions of new software tools, monitoring parameters, tasks, etc. The
benchmark is able to be integrated in different types of equipments, servers,
clients, hardware and software with minimal adaptation effort.

This platform has been promoted by CNES (French Space Center) as a reference
open-source software tool within its research and development studies and
activities in the domain of satellite network communications systems. OpenBACH
has been developped in order to be complementary to OpenSAND, the satellite
network emulator.

The documentation is scattered in this repository through README files at
appropriate places, a table of content is available below. This documentation
is also paired with the [main OpenBACH documentation][1].

OpenBACH is funded and promoted by CNES (French Space Center) as a reference
open-source software tool within its research and development studies and
activities in the domain of satellite communication systems and networks.

OpenBACH EXTRA
==============

This repository contains extra elements for OpenBACH to extend, configure, or
interact with an OpenBACH platform:

 * All [API](api/README.md)s to use openbach with CLI and develop python scripts:
   auditorium scripts, reference scenarios and helpers and data access.
 * All [extra jobs](external_jobs/README.md) not contained by default in OpenBACH.
 * All [executors](executors/README.md) of [reference scenarios](executors/references/README.md)
   and [examples](executors/examples/README.md) maintained in OpenBACH.
 * A tool to [test and validate](validation_suite/README.md) an installed platform.

```
openbach-extra/
├── external_jobs/ 
├── executors/ -> scripts ready to be launched from CLI: allow to run scenarios or
|   |             create scenario JSONs (to be imported in the OpenBACH web interface).
|   ├── reference/ -> executors maintained by the OpenBACH Team
|   └── examples/  -> other examples of executors
├── apis/
|   ├── data_access/
|   ├── auditorium_scripts/
|   └── scenario_builder/
|       ├── helpers/ -> predefined blocks of openbach functions that can be imported in scenarios.
|       └── scenarios/ -> reference scenarios to be imported in your scenarios.
└── validation_suite/ -> automated script to test a platform and the auditorium scripts for regression
```

Cloning OpenBACH-extra on a machine can help manage multiple OpenBACH platforms. 

Get Involved
============

  * See OpenBACH web site: http://www.openbach.org/
  * A mailing list is available: users@openbach.org

Examples of project using OpenBACH
==================================

  * A simple example chaining reference scenarios in python is available [here][2]
  * A project that let you install, set up and run OpenBACH basic scenarios is available [here][3]

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

Copyright © 2016-2020 CNES
OpenBACH is released under GPLv3 (see [LICENSE](LICENSE.md) file).


[1]: https://forge.net4sat.org/openbach/openbach
[2]: https://forge.net4sat.org/openbach/openbach-extra/tree/master/executors/examples
[3]: https://forge.net4sat.org/kuhnn/openbach-example-simple
