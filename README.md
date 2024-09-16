# Day 2 Ops for YugabyteDB  

The contents of this repository are published as an example of how one might write a module to interact with and automate the YBA xCluster DR APIs and other YugabyteDB tools as needed.

The YBA API version used is 2.20 LTS. If you are using a different version, you could expect functionality to change. Reference the following API docs: https://api-docs.yugabyte.com/docs/yugabyte-platform/branches/2.20/f10502c9c9623-yugabyte-db-anywhere-api-overview 

Use common sense and good development practices when testing and preparing to run derivatives of this in your environments.

- [Pre-requisites](#pre-requisites)
- [Run the CLI app](#run-the-cli-app)
    - [Built-in help](#built-in-help)
    - [Configuration options](#configuration-options)
    - [Command-specific notes](#command-specific-notes)
        - [xCluster DR setup](#xcluster-dr-setup)
            - [setup-dr](#setup-dr)
            - [get-dr-config](#get-dr-config)
        - [xCluster DR management](#xcluster-dr-management)
            - [do-pause-xcluster](#do-pause-xcluster)
            - [do-resume-xcluster](#do-resume-xcluster)
            - [do-switchover](#do-switchover)
            - [do-failover](#do-failover)
            - [do-recovery](#do-recovery)
        - [xCluster DR table management](#xcluster-dr-table-management)
            - [get-tables](#get-tables)
            - [do-add-tables-to-dr](#do-add-tables-to-dr)
        - [xCluster DR observability](#xcluster-dr-observability)
            - [obs-latency](#obs-latency)
            - [obs-status](#obs-status)
            - [obs-xcluster](#obs-xcluster)
- [Testing](#testing)
- [Roadmap](#roadmap)

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

![CLI default screen](https://github.com/dataindataout/yb_day2ops/blob/main/images/day2ops_screenshot_main_default.png)

### Built-in help

To review the relevant flags for any command, use the `--help` flag after the command. 

For example: 
```
python src/mainapp.py setup-dr --help 
```

![example help screen](https://github.com/dataindataout/yb_day2ops/blob/main/images/day2ops_screenshot_setupdr_help.png)

### Configuration options

Parameter values can be designated in one of three ways. The values will be read in this order:
- Command-line flags (use the --help option to see the parameter names)
- Configuration files as listed below
- Interactive input (the program will request info missing from flags and files)

`config/auth.yaml` Contains the API key generated within the YBA UI platform, as well as the YBA URL. The APIs are run against that platform; hence the need for the URL.

`config/universe.yaml` Contains the user-friendly names of the source and target universes to be controlled via this CLI app, as well as the databases to be set up with DR and the backup location for the initial backup/restore from the source to the target.

### Command-specific notes

Any of the following commands can be issued via this tool, or via the YBA platform UI. Changes will be seen in both locations. Task IDs shown in the output of the commands can be tracked in the UI as well under the Tasks tab.

#### xCluster DR setup

##### setup-dr                  
Create an xCluster DR configuration. 

Example:
```
python src/mainapp.py setup-dr --xcluster-source-name source-universe-name --xcluster-target-name target-universe-name --replicate-database-names database1,database2 --shared-backup-location name-of-configured-backup-location
```

##### get-dr-config             
Show existing xCluster DR configuration info for the source universe. 

Example:
```
python src/mainapp.py get-dr-config --xcluster-source-name source-universe-name
```

By default, this will show all of the xCluster DR settings in json. You can use the `--key` option to show the value for any key in that larger json. Following are some useful keys:

`--key paused`: indicates if the replication between universes is paused

`--key tables`: list of IDs of tables in replication

`--key tableType`: indicates which API is used for these universes (YCQL or YSQL)

See also the `obs-status` command.

#### xCluster DR management

##### do-pause-xcluster         
Pause the running xCluster DR replication. 

Example:
```
python src/mainapp.py do-pause-xcluster --xcluster-source-name source-universe-name
```

The verification (True or False) will display at the end of this command output.

##### do-resume-xcluster        
Resume the running xCluster DR replication. 

Example:
```
python src/mainapp.py do-resume-xcluster --xcluster-source-name source-universe-name
```

The verification (True or False) will display at the end of this command output.

##### do-switchover             
Switchover the running xcluster replication. A switchover is done gracefully. For example, use switchover when you want to do planned maintenance on universe nodes. The switchover process ensures the active connections are drained, replication is completed, etc.

Requires name of current primary for safety (i.e., to protect you from choosing the wrong universe setup). This will be prompted interactively or you can pass in the `--current-primary` flag. Pass the `--force` flag if you want to avoid the verification prompt.

Example:
```
python src/mainapp.py do-switchover --current-primary source-universe-name
```

##### do-failover               
Failover the running xcluster replication. A failover is done in an emergency situation. For example, use failover when your primary region has a cloud outage. Failovers are immediate and not graceful.

Requires name of current primary for safety (i.e., to protect you from choosing the wrong universe setup). This will be prompted interactively or you can pass in the `--current-primary` flag. Pass the `--force` flag if you want to avoid the verification prompt.

Example:
```
python src/mainapp.py do-failover --current-primary source-universe-name
```

##### do-recovery
After a failover has been issued, xcluster DR replication between the separate universes is no longer running. (Remember, the reason you did a failover is that the original primary region has failed.) When the region has been restored, you can do a recovery. This will bootstrap the current primary back to the old primary and restart replication. If you want to then have the original primary as the current primary, issue a switchover after recovery is complete.

Requires name of current primary for safety (i.e., to protect you from choosing the wrong universe setup). This will be prompted interactively or you can pass in the `--current-primary` flag. Pass the `--force` flag if you want to avoid the verification prompt.

Example:
```
python src/mainapp.py do-recovery --current-primary source-universe-name
```

#### xCluster DR table management

##### get-tables   
Show tables eligible for xCluster DR replication management.

Colocated tables are not eligible for xCluster DR replication, and index tables are included automatically in replication with their parent table.

This display includes output showing which tables are in the xCluster DR replication already.

Example:
```
python src/mainapp.py get-tables --xcluster-source-name source-universe-name
```

You can then add these tables via the `do-add-tables-to-dr` function.

##### do-add-tables-to-dr
Add specified unreplicated table to the xCluster DR configuration. 

Before adding tables to the DR config, be sure that (a) the table definition has been created on both the primary and replica, and (b) the tables are empty. If the table definition is not created on both sides, the process will fail. If the tables are not empty, the entire database/keyspace holding those tables will be bootstrapped, and this can take some time.

Pass comma-delimited table IDs found in `get-tables`. All tables in a given database/keyspace must be added at once. 

Example:
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

Example:
```
python src/mainapp.py obs-latency --xcluster-source-name source-universe-name
```

See https://docs.yugabyte.com/v2.20/yugabyte-platform/back-up-restore-universes/disaster-recovery/disaster-recovery-setup/#metrics for detailed definitions of these metrics.

##### obs-status

Displays the state (configuration), status (replication), primaryUniverseState (source), drReplicaUniverseState (target), and paused values from the xcluster DR config, along with the appropriate definitions. See config/status.yaml for all definitions.

Example:
```
python src/mainapp.py obs-status --xcluster-source-name source-universe-name
```

Notes:
1. The replication state, status, etc. (in particular status="Running" doesn't change if the replication is paused).
2. The replication state, status, etc. don't change if a universe itself is paused.

##### obs-xcluster
Given a universe name, determine if it is a source, target, or neither. If it is a source, show the target universe name. If it is a target, show the source universe name.

Example:
```
python src/mainapp.py obs-xcluster --xcluster-source-name source-universe-name
```

## Testing

You can use `pytest` to execute the provided tests (test_ files). 

### test cluster configuration

You will likely want to use test universes to run tests, not your production universes. Provide a customer ID (unique to a YBA instance) and universe information in the config/testing.yaml file.

### pytest configuration

The configuration for pytest itself is in pytest.ini. 


## Roadmap

Please submit an issue for any requests for features or relative prioritization.

See closed pull requests for more detail on completed items.

### General 
- [x] Initial framework
- [x] Flag for interactive mode (default non-interactive mode)
- [ ] Short flag names
- [ ] Human-readable error handling for interactive mode
- [ ] Return 0 on successful completion; non-zero on failure for non-interactive mode
- [x] All parameters have default values
- [ ] Flag to redirect output to a log file / general logging 
- [x] Add backup location to configuration 
- [x] Add example syntax to all commands
- [ ] Refactor functions to use dynamic source detection instead of configured value

### xCluster DR
- [x] Establish replication between universes
- [x] View and add unreplicated tables
- [x] View replicated tables
- [x] Pause and resume replication
- [x] Switchover (graceful) replication between universes in xCluster DR config
- [x] Failover (immediate) replication between universes in xCluster DR config
- [x] Recover replication between universes after failover
- [x] Remove replication between universes
- [x] Observability: safetime lag
- [x] Observability: status (paused/running and status)
- [x] Observability: current primary
- [ ] Replication lag every x (configurable) seconds
- [ ] Remove tables from replication
- [ ] Resync database 

### DDL wrappers
- [ ] Add table
- [ ] Drop table
- [ ] Alter table
- [ ] Add/drop/alter index
- [ ] Add/drop/alter view

