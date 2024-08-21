# Day 2 Ops for YugabyteDB  

The contents of this repository are published as an example of how one might write a module to interact with and automate the YBA xCluster DR APIs. Use common sense and good development practices when testing and preparing to run derivatives of this in your environments.

Prior to using this module, please review the entire xCluster DR documentation, starting here:
 - https://docs.yugabyte.com/preview/yugabyte-platform/back-up-restore-universes/disaster-recovery/

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

## Plugins used

The following third-party plugins are used:

### Requests
https://requests.readthedocs.io/en/latest/
Used to send http requests to the APIs.

### Typer
https://typer.tiangolo.com/
Typer is the plugin that facilitates running the APIs within a CLI app.

### Tabulate
https://github.com/astanin/python-tabulate
This is used to display results from API calls in a table. It's a nice-to-have, so feel free to rip it out if you don't ever plan to use the app in an interactive fashion.

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

### xCluster DR
- [x] View and add unreplicated tables
- [x] Pause and resume replication
- [x] Switchover (graceful) replication between universes in xCluster DR config
- [ ] Failover (immediate) replication between universes in xCluster DR config
- [ ] Observability: replication lag
- [ ] Observability: safetime
- [ ] Observability: status (stopped/paused/running)
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

