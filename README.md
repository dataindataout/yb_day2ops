# Day 2 Ops for YugabyteDB  

The contents of this repository are published as an example of how one might write a module to interact with and automate the YBA xCluster DR APIs and other YugabyteDB tools as needed.

The YBA API version used is 2.20 LTS. If you are using a different version, you could expect functionality to change. Reference the following API docs: https://api-docs.yugabyte.com/docs/yugabyte-platform/branches/2.20/f10502c9c9623-yugabyte-db-anywhere-api-overview 

Use common sense and good development practices when testing and preparing to run derivatives of this in your environments.

## Notes on using this for xCluster DR

Prior to using this module, please review the entire xCluster DR documentation, starting here:
 - https://docs.yugabyte.com/preview/yugabyte-platform/back-up-restore-universes/disaster-recovery/

The xCluster DR commands do not affect the synchronous replication happening *within* a universe. They are only used to control the asynchronous DR replication established *between* universes (xCluster = cross-cluster). (A YugabyteDB universe is commonly thought of as a cluster of nodes having distributed data within a region or other fault domain.)

## Pre-requisites

You should have Python 3.10+.

The following third-party plugins are used in addition to the standard Python modules. See the requirements.txt file for current versions tested.

### Requests
https://requests.readthedocs.io/en/latest/
Used to send http requests to the APIs.

### Typer
https://typer.tiangolo.com/
Typer is the plugin that facilitates running the APIs within a CLI app.

### PyYAML
https://pyyaml.org/wiki/PyYAMLDocumentation
This is used to parse yaml configuration files.

### Tabulate
https://github.com/astanin/python-tabulate
This is used to display results from API calls in a table. It's a nice-to-have, so feel free to rip it out if you don't ever plan to use the app in an interactive fashion.

## Run the CLI app

The CLI app is started by running `python src/mainapp.py`. It is there you can see the available options.

### Built-in help

To review the relevant flags for any command, use the `--help` flag after the command. 

For example: 
```
python src/mainapp.py setup-dr --help 
```

### Configuration options

The tool currently requires using the configuration files in the `config/` directory. The following describes the contents of the various files in that directory:

`auth.yaml` Contains the API key generated within the YBA UI platform, as well as the YBA URL. The APIs are run against that platform; hence the need for the URL.

`universe.yaml` Contains the user-friendly names of the source and target universes to be controlled via this CLI app, as well as the databases to be set up with DR and the backup location for the initial backup/restore from the source to the target.

### Command-specific notes

Any of the following commands can be issued via this tool, or via the YBA platform UI. Changes will be seen in both locations. Task IDs shown in the output of the commands can be tracked in the UI as well under the Tasks tab.

#### xCluster DR setup

##### setup-dr                  
Create an xCluster DR configuration. Update `config/universe.yaml` and `config/auth.yaml` with the related platform and universe values.

##### get-dr-config             
Show existing xCluster DR configuration info for the source universe. 

By default, this will show all of the xCluster DR settings in json. You can use the `--key` option to show the value for any key in that larger json. Following are some useful keys:

`--key paused`: indicates if the replication between universes is paused

`--key tables`: list of IDs of tables in replication

`--key tableType`: indicates which API is used for these universes (YCQL or YSQL)

See also the `obs-status` command.

#### xCluster DR management

##### do-pause-xcluster         
Pause the running xCluster DR replication. Verify with `get-dr-config --key paused`. If successful, this value will be `True`.

##### do-resume-xcluster        
Resume the running xCluster DR replication. Verify with `get-dr-config --key paused`. If successful, this value will be `False`.

##### do-switchover             
Switchover the running xcluster replication. A switchover is done gracefully. For example, use switchover when you want to do planned maintenance on universe nodes. The switchover process ensures the active connections are drained, replication is completed, etc.

Requires name of current primary for safety (i.e., to protect you from choosing the wrong universe setup). This will be prompted interactively or you can pass in the `--current-primary` flag. Pass the `--force` flag if you want to avoid the verification prompt.

##### do-failover               
Failover the running xcluster replication. A failover is done in an emergency situation. For example, use failover when your primary region has a cloud outage. Failovers are immediate and not graceful.

Requires name of current primary for safety (i.e., to protect you from choosing the wrong universe setup). This will be prompted interactively or you can pass in the `--current-primary` flag. Pass the `--force` flag if you want to avoid the verification prompt.

##### do-recovery
After a failover has been issued, xcluster DR replication between the separate universes is no longer running. (Remember, the reason you did a failover is that the original primary region has failed.) When the region has been restored, you can do a recovery. This will bootstrap the current primary back to the old primary and restart replication. If you want to then have the original primary as the current primary, issue a switchover after recovery is complete.

Requires name of current primary for safety (i.e., to protect you from choosing the wrong universe setup). This will be prompted interactively or you can pass in the `--current-primary` flag. Pass the `--force` flag if you want to avoid the verification prompt.

#### xCluster DR table management

##### get-unreplicated-tables   
Show tables that have not been added to the xCluster DR replication. You can then add these tables via the `do-add-tables-to-dr` function.

##### do-add-tables-to-dr
Add specified unreplicated table to the xCluster DR configuration. 

Before adding tables to the DR config, be sure that (a) the table definition has been created on both the primary and replica, and (b) the tables are empty. If the table definition is not created on both sides, the process will fail. If the tables are not empty, the entire database/keyspace holding those tables will be bootstrapped, and this can take some time.

Pass comma-delimited table IDs found in `get-unreplicated-tables`. All tables in a given database/keyspace must be added at once. For example:
```
python src/mainapp.py do-add-tables-to-dr --add-table-ids "00004702000030008000000000004003,00004702000030008000000000004000"
```

#### xCluster DR observability

##### obs-latency

Displays the following metrics:

- safetime timestamp (in UTC)
- safetime lag
- safetime skew
- estimated amount of potential data loss on *failover* (remember failover is urgent, unlike the graceful switchover)

See https://docs.yugabyte.com/v2.20/yugabyte-platform/back-up-restore-universes/disaster-recovery/disaster-recovery-setup/#metrics for detailed definitions of these metrics.

##### obs-status

Displays the state, status, primaryUniverseState, drReplicaUniverseState, and paused values from the xcluster DR config.

---

`state` values (status of the DR configuration)

`state: Initializing` - DR replication is being initialized between source and target

`state: Replicating` - DR replication has been established between source and target

`state: Switchover in Progress` - the replication stream is in the process of switching over

`state: Failover in Progress` - the replication stream is in the process of failing over

`state: Halted` - DR replication was halted during failover because data is not in sync between source and target

`state: Error` - an error was experienced during replication (re)configuration

---

`status` values (status of the DR replication stream)


`status: Initialized` - the configuration has been applied, but replication is not yet running

`status: Running` - the configured DR xcluster replication is running (but may be paused)

`status: Updating` - the DR xcluster configuration is being changed for this stream

`status: DeletedUniverse` - either the source or the target has been force-deleted

`status: DeletionFailed` - removing the async replication config has failed

`status: Failed` - an error was experienced during replication (re)configuration

---

`primaryUniverseState` values (status of the source side of the replication stream)


`primaryUniverseState: Unconfigured for DR` - this universe is not part of an xcluster DR configuration 

`primaryUniverseState: Ready to replicate` - checkpoints have been established on the source tables

`primaryUniverseState: Waiting for DR` - before bootstrapping, the source is waiting for a configured time to give the target time to drop the database to be replicated (if present)

`primaryUniverseState: Replicating data` - source is sending data to target without issue

`primaryUniverseState: Preparing for switchover` - source is waiting for all remaining changes to be replicated to target

`primaryUniverseState: Switching to DR replica` - DR configuration is changing to make this the target

`primaryUniverseState: Universe marked as DR failed` - a repair is required to restore the DR replication, probably after failover

---

`drReplicaUniverseState` values (status of the target side of the replication stream)


`drReplicaUniverseState: Unconfigured for DR` - this universe is not part of an xcluster DR configuration

`drReplicaUniverseState: Bootstrapping` - a full copy (backup/restore) is being done from the source

`drReplicaUniverseState: Receiving data, Ready for reads` - target is receiving data from source without issue

`drReplicaUniverseState: Switching to DR primary` - DR configuration is changing to make this the source

`drReplicaUniverseState: Universe marked as DR failed` - a repair is required to restore the DR replication, probably after failover

---

`paused`


`paused: True` - DR replication has been paused, and no data is being replicated between source and target

`paused: False` - DR replication has not been paused (has never been paused or was resumed after being paused), and so data is being replicated between source and target

---

Notes:
1. The replication state, status, etc. (in particular status="Running" doesn't change if the replication is paused).
2. The replication state, status, etc. don't change if a universe itself is paused.

## Roadmap

Please submit an issue for any requests for features or relative prioritization.

See closed pull requests for more detail on completed items.

### General 
- [x] Initial framework
- [ ] Flag for interactive mode (default non-interactive mode)
- [ ] Short flag names
- [ ] Human-readable error handling for interactive mode
- [ ] Return 0 on successful completion; non-zero on failure for non-interactive mode
- [ ] All parameters have default values
- [ ] Flag to redirect output to a log file / general logging 
- [ ] Add backup location to configuration 
- [ ] Add example syntax to all commands

### xCluster DR
- [x] Establish replication between universes
- [x] View and add unreplicated tables
- [ ] View replicated tables
- [x] Pause and resume replication
- [x] Switchover (graceful) replication between universes in xCluster DR config
- [x] Failover (immediate) replication between universes in xCluster DR config
- [x] Recover replication between universes after failover
- [ ] Remove replication between universes
- [x] Observability: safetime lag
- [ ] Observability: status (paused/running and status)
- [ ] Observability: current primary
- [ ] Replication lag every x (configurable) seconds
- [ ] View replicated tables
- [ ] Remove tables from replication
- [ ] Resync database 

### DDL wrappers
- [ ] Add table
- [ ] Drop table
- [ ] Alter table
- [ ] Add/drop/alter index
- [ ] Add/drop/alter view

