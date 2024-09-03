import yaml

import typer
from typing import List

from pathlib import Path
from pprint import pprint
from typing_extensions import Annotated

from core.internal_rest_apis import (
    _get_session_info,
)
from core.get_universe_info import get_universe_uuid_by_name
from includes.overrides import suppress_warnings
from xclusterdr.manage_dr_cluster import (
    create_xcluster_dr,
    get_xcluster_dr_available_tables,
    add_tables_to_xcluster_dr,
    pause_xcluster,
    resume_xcluster,
    perform_xcluster_dr_switchover,
    perform_xcluster_dr_failover,
    perform_xcluster_dr_recovery,
)
from xclusterdr.common import get_source_xcluster_dr_config
from xclusterdr.observability import get_xcluster_dr_safetimes, get_status

suppress_warnings()

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich", add_completion=False)
state = {"verbose": False}

# get universe config values


def get_xcluster_source_name():
    demo_config_file = Path("config/universe.yaml")
    demo_config_data = yaml.safe_load(demo_config_file.read_text())
    xcluster_source_name = demo_config_data["XCLUSTER_SOURCE"]
    return xcluster_source_name


def get_xcluster_target_name():
    demo_config_file = Path("config/universe.yaml")
    demo_config_data = yaml.safe_load(demo_config_file.read_text())
    xcluster_target_name = demo_config_data["XCLUSTER_TARGET"]
    return xcluster_target_name


def get_xcluster_replicate_database_names():
    demo_config_file = Path("config/universe.yaml")
    demo_config_data = yaml.safe_load(demo_config_file.read_text())
    replicate_database_names = demo_config_data["REPLICATE_DATABASE_NAMES"]
    return replicate_database_names


# get auth config values


def get_customer_uuid():
    user_session = _get_session_info()
    customer_uuid = user_session["customerUUID"]
    return customer_uuid


# generic helper functions


def get_xcluster_source_uuid():
    source_universe_uuid = get_universe_uuid_by_name(
        get_customer_uuid(), get_xcluster_source_name()
    )
    return source_universe_uuid


def get_xcluster_target_uuid():
    target_universe_uuid = get_universe_uuid_by_name(
        get_customer_uuid(), get_xcluster_target_name()
    )
    return target_universe_uuid


def parse_comma_separated_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


# the app commands


## app commands: xCluster DR replication setup


@app.command("setup-dr", rich_help_panel="xCluster DR Replication Setup")
def create_xluster_dr_configuration(
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str, typer.Argument(default_factory=get_xcluster_source_name)
    ],
    xcluster_target_name: Annotated[
        str, typer.Argument(default_factory=get_xcluster_target_name)
    ],
    replicate_database_names: Annotated[
        str, typer.Argument(default_factory=get_xcluster_replicate_database_names)
    ],
):
    """
    Create an xCluster DR configuration
    """
    create_xcluster_dr(
        customer_uuid,
        xcluster_source_name,
        xcluster_target_name,
        replicate_database_names,
    )


@app.command("get-dr-config", rich_help_panel="xCluster DR Replication Setup")
def get_xcluster_configuration_info(
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str, typer.Argument(default_factory=get_xcluster_source_name)
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
    force: Annotated[
        bool,
        typer.Option(
            prompt="Are you sure you want to pause the replication for these clusters?"
        ),
    ],
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str, typer.Argument(default_factory=get_xcluster_source_name)
    ],
):
    """
    Pause the running xCluster DR replication
    """
    if force:
        return pause_xcluster(customer_uuid, xcluster_source_name)
    else:
        print("Operation cancelled")


@app.command("do-resume-xcluster", rich_help_panel="xCluster DR Replication Management")
def do_resume_xcluster(
    force: Annotated[
        bool,
        typer.Option(
            prompt="Are you sure you want to resume the replication for these clusters?"
        ),
    ],
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str, typer.Argument(default_factory=get_xcluster_source_name)
    ],
):
    """
    Resume the active xCluster DR replication
    """
    if force:
        return resume_xcluster(customer_uuid, xcluster_source_name)
    else:
        print("Operation cancelled")


@app.command("do-switchover", rich_help_panel="xCluster DR Replication Management")
def do_switchover(
    current_primary: Annotated[
        str,
        typer.Option(
            prompt="Please provide the name of the current primary for verification"
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            prompt="You are about to perform a switchover of the primary cluster. Please confirm. "
        ),
    ],
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
):
    """
    Switchover the running xCluster DR replication
    """
    if force:
        try:
            return perform_xcluster_dr_switchover(customer_uuid, current_primary)
        except RuntimeError as e:
            print(f"There was a RuntimeError: {e}")
    else:
        print("Operation cancelled")


@app.command("do-failover", rich_help_panel="xCluster DR Replication Management")
def do_failover(
    current_primary: Annotated[
        str,
        typer.Option(
            prompt="Please provide the name of the current primary for verification"
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            prompt="You are about to perform an emergency failover to the replica cluster. XCLUSTER REPLICATION BETWEEN PRIMARY AND REPLICA UNIVERSES WILL BE STOPPED AFTER THIS UNTIL YOU RECOVER IT. Please confirm. "
        ),
    ],
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
):
    """
    Failover (immediately, non-gracefully) the running xCluster DR replication
    """
    if force:
        try:
            return perform_xcluster_dr_failover(customer_uuid, current_primary)
        except RuntimeError as e:
            print(f"There was a RuntimeError: {e}")
    else:
        print("Operation cancelled")


@app.command("do-recovery", rich_help_panel="xCluster DR Replication Management")
def do_recovery(
    current_primary: Annotated[
        str,
        typer.Option(
            prompt="Please provide the name of the current primary for verification"
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            prompt="You are about to perform a recovery on xCluster DR replication previously failed over. This will restore the replication stream. Please confirm. "
        ),
    ],
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
):
    """
    Recovery restores replication that previously had a non-graceful failover
    """
    if force:
        try:
            return perform_xcluster_dr_recovery(customer_uuid, current_primary)
        except RuntimeError as e:
            print(f"There was a RuntimeError: {e}")
    else:
        print("Operation cancelled")


## app commands: xCluster DR replication table management


@app.command(
    "get-unreplicated-tables",
    rich_help_panel="xCluster DR Replication Table Management",
)
def get_xcluster_dr_unreplicated_tables(
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str,
        typer.Argument(default_factory=get_xcluster_source_name),
    ],
):
    """
    Show tables that have not been added to the xCluster DR replication
    """
    print(get_xcluster_dr_available_tables(customer_uuid, xcluster_source_name))


@app.command(
    "do-add-tables-to-dr", rich_help_panel="xCluster DR Replication Table Management"
)
def do_add_tables_to_dr(
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str, typer.Argument(default_factory=get_xcluster_source_name)
    ],
    add_table_ids: Annotated[
        str,
        typer.Option(
            help='Comma-separated list of IDs (example: "id1, id2")',
            callback=parse_comma_separated_list,
        ),
    ],
):
    """
    Add specified unreplicated table to the xCluster DR configuration
    """
    if add_table_ids:
        return add_tables_to_xcluster_dr(
            customer_uuid, xcluster_source_name, add_table_ids
        )
    else:
        print("Please provide table IDs. Operation cancelled.")


## app commands: xCluster DR observability


@app.command("obs-latency", rich_help_panel="xCluster DR Replication Observability")
def get_observability_safetime_lag(
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str, typer.Argument(default_factory=get_xcluster_source_name)
    ],
):
    """
    Retrieve latency and safetime metrics
    """
    print(get_xcluster_dr_safetimes(customer_uuid, xcluster_source_name))


@app.command("obs-status", rich_help_panel="xCluster DR Replication Observability")
def get_observability_status(
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str, typer.Argument(default_factory=get_xcluster_source_name)
    ],
):
    """
    Retrieve status, state, etc.
    """
    print(get_status(customer_uuid, xcluster_source_name))


## the app callback


@app.callback()
def main(verbose: bool = False):
    """
    Please update config/auth.yaml and config/universe.yaml with appropriate values for your universe.
    """
    if verbose:
        print("Will write verbose output")
        state["verbose"] = True


if __name__ == "__main__":
    app()
