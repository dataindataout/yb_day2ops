import typer
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


# the app commands


## app commands: xcluster dr replication utilities


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
