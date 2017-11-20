External Jobs Repository for the OpenBACH platform
==================================================

This project contains jobs developed for different studies, two groups are identified:

 * stable jobs: these jobs are correctly validated and operational but may be too specific for an inclusion in core;
 * experimental jobs: these jobs are either not fully validated for all possible uses or not maintained anymore.

Usage
-----

To include these jobs in your OpenBACH platform, clone this repository or download an archive and then, on the
OpenBACH installation command line, specify the folder from which you want to use jobs:


    ansible-playbook install -u <your_user> -k -K -e '{"openbach_jobs_folders": ["~/openbach-external-jobs/stable_jobs/", "~/openbach-external-jobs/experimental_jobs/"]}'
