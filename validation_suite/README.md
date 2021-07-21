# Validation Suite

The Validation Suite is a Python script that automate calling most of the auditorium scripts on a given platform.
Its aim is to help developers keep track of regressions or errors on either the auditorium scripts or the core
of OpenBACH.

## Expected Infrastructure

Most tests and executors can be run on one or two agents, but the `data_transfer_configure_link` executor requires
a client, a server and a middlebox as 3 separate entities; which makes it the minimum number of agents required to
run the test suite.

The middlebox should be configured so it can route packets to each of the other two agents. The client and the server
merely requires being able to send traffic to the middlebox. The `ip_route` job will setup a route on each of them to
use the middlebox to send traffic to the other one. This means you may be able to use either kind of infrastructure:

```
              [Middlebox]                                                  [Middlebox]
                |     |                             or                          |
[Client]———————(=)   (=)——————[Server]                       [Client]——————————(=)——————————[Server]
```

These machine need not be added as agents in the OpenBach platform prior to the use of the validation suite. The script
will make sure to check which are present and which are not and to install agents as needed on the machines that are
not already. The script will also try to backup the jobs installed on the existing agents and remove the extraneous
ones that it needed installed to perform the tests. All in all, the script will try to leave the platform in a state
similar to what it was before being launched.

## Expected Arguments

The script will need to know about the 3 machines that will be used to run the various tests:

  * The server: its public IP address must be supplied (using the `-s` flag) so an agent can be installed onto it. If
    an agent is already installed, please use the IP address that OpenBach already know of so the script is aware that
    this agent exists. If its IP address to talk to/from the middlebox is different than its public address, please
    provide it using the `-S` flag.
  * The client: its public IP address must be supplied (using the `-c` flag) so an agent can be installed onto it. If
    an agent is already installed, please use the IP address that OpenBach already know of so the script is aware that
    this agent exists. If its IP address to talk to/from the middlebox is different than its public address, please
    provide it using the `-C` flag.
  * The middlebox: its public IP address must be supplied (using the `-m` flag) so an agent can be installed onto it.
    If an agent is already installed, please use the IP address that OpenBach already know of so the script is aware
    that this agent exists. If its IP address known from the client or the server is different than its public address,
    please provide it using the `-M` flag as it will be used as the `gateway_ip` parameter of the `ip_route` job on
    the client and the server. You must also provide a comma-separated list of interfaces where the `configure_link`
    job will apply / clear restrictions through the use of the `data_transfer_configure_link` executor.

The script also allows you to specify extraneous IP addresses where you would like to try the installation of an agent
(using the `-e` flag as many time as deemed necessary).

And since agents will be installed through this script, you may need to provide additional connection informations: the
user (which default to the user executing the script) responsible of creating an SSH connection to the agents being
installed (using the `-u` flag) and the password for said user (using the `-p` flag). If no password is provided, the
SSH connection will rely on private keys on the controller that can be configured through the `~openbach/.ssh/config`
file.

Lastly, since this script uses a `ScenarioObserver` it is akin to an executor, so you may provide it with informations
pertaining to the controller using either a `controller` file in the current directory or the `--controller`, `--login`
and `--password` command-line arguments.

## Expected Behaviour

After parsing the command-line and using a few calls to check the projects and agents registered in the controller, the
validation suite will perform the following actions:

  * Make a backup of the jobs installed on agents that are neither reserved nor used in any project
  * Uninstall these agents
  * List the existing collectors
  * Install all the agents (those just uninstalled + the ones missing from the mandatory machines + the extraneous ones from the `-e` flag on the command line)
  * Find a machine in these installed agents that has no collector already installed and, if found:
    * Install a collector
    * Change the collector assigned to this agent back to its old collector
    * Delete the collector
    * Reinstall the agent (as deleting a collector also delete its associated agent)
  * Create a new project to run scenarios in and save the JSON response for future use
  * Modify the project to add a description
  * Remove the project
  * Dump the previous JSON response into a file to Add a new project from the file
  * List (again) the available agents for this new project to check for discrepancies
  * Add an entity into the project for each available agent
  * Add an entity into the project without an associated agent
  * List entities of the project
  * Remove all entities from the project
  * Add 3 entities to the project, one for the client, one for the server, and one for the middlebox
  * List the jobs available on the controller
  * List the jobs available in the `external_jobs/stable_jobs` folder
  * Add the external jobs to the controller
  * Install a random subset of 4 of the external jobs into each of the agents
  * get a Status of each job installation for each agent to assert it was completed
  * Remove these installed jobs from the agents
  * Install the required jobs for each scenario on the 3 mandatory agents
  * Create an empty scenario in the project
  * Modify the scenario to populate its content from a file
  * Add a second scenario directly from a file
  * Start both scenarios
  * get the Status of the scenarios until the first one stops itself
  * Stop the second scenario
  * Retrieve the scenario instance data of the first scenario (CSV)
  * Remove both scenarios
  * Start the job `fping` several times on a randomly selected agent
  * List the job instances on said agent
  * Stop the last launched job instance
  * Stop all remaining job instances
  * get a Status of the job instances on the agent to make sure everything is stopped properly
  * Run some executors:
    * Data transfer configure link
    * Network Delay
    * Network Jitter
    * Network Rate
    * Network One Way Delay
    * Network Global
    * Service FTP
    * Service Video Dash
    * Service VoIP
    * Service Web Browsing
    * Service Traffic Mix
    * Transport TCP One Flow
  * Remove the project
  * Uninstall all previously installed agents
  * Reinstall previously existing agents and restore their installed jobs
