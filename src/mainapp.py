import typer
from typing import List

import yaml

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
    get_source_xcluster_dr_config,
    get_xcluster_dr_available_tables,
    add_tables_to_xcluster_dr,
)

suppress_warnings()

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
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


## app commands: xcluster dr replication utilities


@app.command(
    "get-unreplicated-tables", rich_help_panel="xCluster DR Replication Utilities"
)
def get_xcluster_dr_unreplicated_tables(
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str,
        typer.Argument(default_factory=get_xcluster_source_name),
    ],
):
    """
    Show tables that have not been added to the xcluster dr replication
    """
    print(get_xcluster_dr_available_tables(customer_uuid, xcluster_source_name))


@app.command("setup-dr", rich_help_panel="xCluster DR Replication Utilities")
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
    Create an xcluster dr configuration
    """
    create_xcluster_dr(
        customer_uuid,
        xcluster_source_name,
        xcluster_target_name,
        replicate_database_names,
    )


@app.command("get-dr-config", rich_help_panel="xCluster DR Replication Utilities")
def get_xcluster_configuration_info(
    customer_uuid: Annotated[str, typer.Argument(default_factory=get_customer_uuid)],
    xcluster_source_name: Annotated[
        str, typer.Argument(default_factory=get_xcluster_source_name)
    ],
):
    """
    Show existing xcluster dr configuration info for the source universe
    """
    pprint(get_source_xcluster_dr_config(customer_uuid, xcluster_source_name))


@app.command("do-add-tables-to-dr", rich_help_panel="xCluster DR Replication Utilities")
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
    Add specified unreplicated table to the xCluster DR configuration to be replicated.
    """
    if add_table_ids:
        return add_tables_to_xcluster_dr(
            customer_uuid, xcluster_source_name, add_table_ids
        )
    else:
        print("Please provide table IDs. Operation cancelled.")


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
