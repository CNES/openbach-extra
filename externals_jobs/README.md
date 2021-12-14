External Jobs Repository for the OpenBACH platform
==================================================

Some jobs are installed by default on an OpenBACH platform. 

The external jobs of the OpenBACH-extra project are a set of jobs that must be added to an
OpenBACH controller for being used on a specific OpenBACH plateform. 

This project contains jobs developed for different studies, two groups are identified:

  * stable jobs: these jobs are correctly validated and operational but may be too
    specific for an inclusion in core;
  * experimental jobs: these jobs are either not fully validated for all possible
    uses or not maintained anymore.

Usage
-----

To include these jobs in your OpenBACH platform, clone this repository or download an archive and
then, on the OpenBACH installation command line, specify the folder from which you want to use jobs:

```
ansible-playbook install -u <your_user> -k -K -e '{"openbach_jobs_folders": ["~/openbach-extra/externals_jobs/stable_jobs/", "~/openbach-extra/externals_jobs/experimental_jobs/"]}'
```

You can also add these jobs in the controller, one by one, from the menu in the administrative part
of the Auditorium Web Interface.
