import os
import yaml

import typer
from typing import List

from pprint import pprint
from typing_extensions import Annotated

from core.internal_rest_apis import (
    _get_session_info,
)
from core.get_universe_info import get_universe_uuid_by_name

from includes.get_demo_config import get_config
from includes.overrides import suppress_warnings
from includes.validation import command_confirmed

from xclusterdr.manage_dr_cluster import (
    create_xcluster_dr,
    delete_xcluster_dr,
    get_xcluster_tables,
    add_tables_to_xcluster_dr,
    pause_xcluster,
    resume_xcluster,
    perform_xcluster_dr_switchover,
    perform_xcluster_dr_failover,
    perform_xcluster_dr_recovery,
)
from xclusterdr.common import get_source_xcluster_dr_config

from xclusterdr.observability import (
    get_xcluster_dr_safetimes,
    get_status,
    get_all_clusters,
)

from healthcheck.map import get_diagram_map

suppress_warnings()

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)
state = {"verbose": False}


# get auth config values


def get_customer_uuid():
    user_session = _get_session_info()
    customer_uuid = user_session["customerUUID"]
    return customer_uuid


# generic helper functions


def get_xcluster_source_uuid():
    source_universe_uuid = get_universe_uuid_by_name(
        get_customer_uuid(), os.getenv("XCLUSTER_SOURCE")
    )
    return source_universe_uuid


def get_xcluster_target_uuid():
    target_universe_uuid = get_universe_uuid_by_name(
        get_customer_uuid(), os.getenv("XCLUSTER_TARGET")()
    )
    return target_universe_uuid


def parse_comma_separated_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


# the app commands


## app commands: xCluster DR replication setup


@app.command("setup-dr", rich_help_panel="xCluster DR Replication Setup")
def create_xluster_dr_configuration(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    xcluster_source_name: Annotated[
        str, typer.Option(envvar="XCLUSTER_SOURCE", prompt=True)
    ],
    xcluster_target_name: Annotated[
        str, typer.Option(envvar="XCLUSTER_TARGET", prompt=True)
    ],
    replicate_database_names: Annotated[
        str, typer.Option(envvar="REPLICATE_DATABASE_NAMES", prompt=True)
    ],
    shared_backup_location: Annotated[
        str, typer.Option(envvar="SHARED_BACKUP_LOCATION", prompt=True)
    ],
    force: Annotated[bool, typer.Option("--force")] = False,
):
    """
    Create an xCluster DR configuration
    """
    confirmation_text = f"You are about to set up xCluster DR async replication of the database(s) {replicate_database_names} between the source universe {xcluster_source_name} and the target universe {xcluster_target_name}. The backup storage you'll use for the initial bootstrapping is {shared_backup_location}. Is this what you want to do?"

    if force or command_confirmed(confirmation_text):
        create_xcluster_dr(
            customer_uuid,
            xcluster_source_name,
            xcluster_target_name,
            replicate_database_names,
            shared_backup_location,
        )
    else:
        print(f"OK. Command cancelled.")


@app.command("remove-dr", rich_help_panel="xCluster DR Replication Setup")
def create_xluster_dr_configuration(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    universe_name: Annotated[str, typer.Option(envvar="XCLUSTER_SOURCE", prompt=True)],
    force: Annotated[bool, typer.Option("--force")] = False,
):
    """
    Remove an xCluster DR configuration
    """
    confirmation_text = f"You are about to remove the xCluster DR async replication between {universe_name} and its target. If you want to set it back up, you will need to re-bootstrap the data. Is this what you want to do?"

    if force or command_confirmed(confirmation_text):
        delete_xcluster_dr(
            customer_uuid,
            universe_name,
        )
    else:
        print(f"OK. Command cancelled.")


@app.command("get-dr-config", rich_help_panel="xCluster DR Replication Setup")
def get_xcluster_configuration_info(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    xcluster_source_name: Annotated[
        str, typer.Option(envvar="XCLUSTER_SOURCE", prompt=True)
    ],
    key: Annotated[
        str,
        typer.Option(
            help="A single key to return the value from the DR config (example: paused)",
        ),
    ] = "all",
):
    """
    Show existing xCluster DR configuration info for the source universe
    """
    pprint(get_source_xcluster_dr_config(customer_uuid, xcluster_source_name, key))


## app commands: xCluster DR replication management


@app.command("do-pause-xcluster", rich_help_panel="xCluster DR Replication Management")
def do_pause_xcluster(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    xcluster_source_name: Annotated[
        str, typer.Option(envvar="XCLUSTER_SOURCE", prompt=True)
    ],
    force: Annotated[bool, typer.Option("--force")] = False,
):
    """
    Pause the running xCluster DR replication
    """
    confirmation_text = f"You are about to pause the xCluster DR async replication between the source universe {xcluster_source_name} and its target universe. Is this what you want to do?"

    if force or command_confirmed(confirmation_text):
        return pause_xcluster(customer_uuid, xcluster_source_name)
    else:
        print(f"OK. Command cancelled.")


@app.command("do-resume-xcluster", rich_help_panel="xCluster DR Replication Management")
def do_resume_xcluster(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    xcluster_source_name: Annotated[
        str, typer.Option(envvar="XCLUSTER_SOURCE", prompt=True)
    ],
    force: Annotated[bool, typer.Option("--force")] = False,
):
    """
    Resume the active xCluster DR replication
    """
    confirmation_text = f"You are about to resume the xCluster DR async replication between the source universe {xcluster_source_name} and its target universe. Is this what you want to do?"

    if force or command_confirmed(confirmation_text):
        return resume_xcluster(customer_uuid, xcluster_source_name)
    else:
        print(f"OK. Command cancelled.")


@app.command("do-switchover", rich_help_panel="xCluster DR Replication Management")
def do_switchover(
    current_primary: Annotated[
        str,
        typer.Option(
            prompt="Please provide the name of the current source universe for verification"
        ),
    ],
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    force: Annotated[bool, typer.Option("--force")] = False,
):
    """
    Switchover the running xCluster DR replication
    """
    confirmation_text = f"You are about to do a switchover of the xCluster DR async replication between the source universe {current_primary} and its target universe. Is this what you want to do?"

    if force or command_confirmed(confirmation_text):
        try:
            return perform_xcluster_dr_switchover(customer_uuid, current_primary)
        except RuntimeError as e:
            print(f"There was a RuntimeError: {e}")
    else:
        print(f"OK. Command cancelled.")


@app.command("do-failover", rich_help_panel="xCluster DR Replication Management")
def do_failover(
    current_primary: Annotated[
        str,
        typer.Option(
            prompt="Please provide the name of the current primary for verification"
        ),
    ],
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    force: Annotated[bool, typer.Option("--force")] = False,
):
    """
    Failover (immediately, non-gracefully) the running xCluster DR replication
    """
    confirmation_text = f"You are about to do an emergency failover of the xCluster DR async replication between the source universe {current_primary} and its target universe. You will need to run a recovery in order to re-establish DR, and this will probably require a re-bootstrap of all data. Is this what you want to do?"

    if force or command_confirmed(confirmation_text):
        try:
            return perform_xcluster_dr_failover(customer_uuid, current_primary)
        except RuntimeError as e:
            print(f"There was a RuntimeError: {e}")
    else:
        print(f"OK. Command cancelled.")


@app.command("do-recovery", rich_help_panel="xCluster DR Replication Management")
def do_recovery(
    current_primary: Annotated[
        str,
        typer.Option(
            prompt="Please provide the name of the current primary for verification"
        ),
    ],
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    force: Annotated[bool, typer.Option("--force")] = False,
):
    """
    Recovery restores replication that previously had a non-graceful failover
    """
    confirmation_text = f"You are about to do a recovery of the xCluster DR async replication between the source universe {current_primary} and its target universe. This will probably require a re-bootstrap of all data. Is this what you want to do?"

    if force or command_confirmed(confirmation_text):
        try:
            return perform_xcluster_dr_recovery(customer_uuid, current_primary)
        except RuntimeError as e:
            print(f"There was a RuntimeError: {e}")
    else:
        print(f"OK. Command cancelled.")


## app commands: xCluster DR replication table management


@app.command(
    "get-tables",
    rich_help_panel="xCluster DR Replication Table Management",
)
def get_xcluster_dr_unreplicated_tables(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    xcluster_source_name: Annotated[
        str, typer.Option(envvar="XCLUSTER_SOURCE", prompt=True)
    ],
    force: Annotated[bool, typer.Option("--force")] = False,
):
    """
    Show tables eligible for xCluster DR replication management
    """
    confirmation_text = f"This will show the list of tables on the source universe {xcluster_source_name}, both replicated and unreplicated. You can add tables using the do-add-tables-to-dr command. OK?"

    if force or command_confirmed(confirmation_text):
        print(get_xcluster_tables(customer_uuid, xcluster_source_name))
    else:
        print(f"OK. Command cancelled.")


@app.command(
    "do-add-tables-to-dr", rich_help_panel="xCluster DR Replication Table Management"
)
def do_add_tables_to_dr(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    xcluster_source_name: Annotated[
        str, typer.Option(envvar="XCLUSTER_SOURCE", prompt=True)
    ],
    add_table_ids: Annotated[
        str,
        typer.Option(
            help='Comma-separated list of IDs (example: "id1,id2")',
            callback=parse_comma_separated_list,
        ),
    ],
    force: Annotated[bool, typer.Option("--force")] = False,
):
    """
    Add specified unreplicated table to the xCluster DR configuration
    """
    confirmation_text = f"You are about to add the tables {add_table_ids} to the xCluster DR async replication stream between the source universe {xcluster_source_name} and its target universe. Is this what you want to do?"

    if force or command_confirmed(confirmation_text):
        if add_table_ids:
            return add_tables_to_xcluster_dr(
                customer_uuid, xcluster_source_name, add_table_ids
            )
        else:
            print("Please provide table IDs. Command cancelled.")
    else:
        print(f"OK. Command cancelled.")


## app commands: xCluster DR observability


@app.command("obs-latency", rich_help_panel="xCluster DR Replication Observability")
def get_observability_safetime_lag(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    xcluster_source_name: Annotated[
        str, typer.Option(envvar="XCLUSTER_SOURCE", prompt=True)
    ],
):
    """
    Retrieve latency and safetime metrics
    """
    print(get_xcluster_dr_safetimes(customer_uuid, xcluster_source_name))


@app.command("obs-status", rich_help_panel="xCluster DR Replication Observability")
def get_observability_status(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    xcluster_source_name: Annotated[
        str, typer.Option(envvar="XCLUSTER_SOURCE", prompt=True)
    ],
):
    """
    Retrieve status, state, etc.
    """
    print(get_status(customer_uuid, xcluster_source_name))


@app.command("obs-xcluster", rich_help_panel="xCluster DR Replication Observability")
def get_all_clusters_for_yba(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
):
    """
    Show info for all universes
    """
    print(get_all_clusters(customer_uuid))


## app commands: healthcheck


@app.command("diagram", rich_help_panel="Healthcheck")
def show_diagram(
    customer_uuid: Annotated[
        str, typer.Argument(default_factory=get_customer_uuid, hidden=True)
    ],
    universe_name: Annotated[str, typer.Option(envvar="UNIVERSE", prompt=True)],
):
    """
    Create network diagram for provided universe name
    """
    return get_diagram_map(customer_uuid, universe_name)


## the app callback


@app.callback()
def main(
    config: str = typer.Option(
        None, "--config", "-c", help="Path to the config file (optional)"
    ),
):
    if config:
        typer.echo(f"Using config file: {config}")
        get_config(config)


if __name__ == "__main__":
    app()
