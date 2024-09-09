import tabulate

import datetime
import pytz
import yaml

from core.internal_rest_apis import (
    _get_xcluster_dr_safetime,
    _get_universe_by_name,
    _get_universe_by_uuid,
    _get_xcluster_dr_configs,
)

from xclusterdr.common import get_source_xcluster_dr_config


def get_xcluster_dr_safetimes(customer_uuid: str, source_universe_name: str):

    get_source_universe_response = _get_universe_by_name(
        customer_uuid, source_universe_name
    )
    source_universe_details = next(iter(get_source_universe_response), None)
    if source_universe_details is None:
        raise RuntimeError(
            f"ERROR: the universe '{source_universe_name}' was not found."
        )
    else:
        dr_config_uuid = get_source_xcluster_dr_config(
            customer_uuid, source_universe_name, "uuid"
        )

        safetime_by_keyspace_list = _get_xcluster_dr_safetime(
            customer_uuid, dr_config_uuid
        )

        print(
            "See the following for details on these metrics: https://docs.yugabyte.com/v2.20/yugabyte-platform/back-up-restore-universes/disaster-recovery/disaster-recovery-setup/#metrics"
        )

        formatted_safetime_by_keyspace_list = []
        for i in safetime_by_keyspace_list["safetimes"]:
            new_row = [
                i["namespaceName"],
                datetime.datetime.fromtimestamp(
                    i["safetimeEpochUs"] / 1000 / 1000, pytz.UTC
                ),
                i["safetimeLagUs"] / 1000,
                i["safetimeSkewUs"] / 1000,
                i["estimatedDataLossMs"],
            ]
            formatted_safetime_by_keyspace_list.append(new_row)

        return tabulate.tabulate(
            formatted_safetime_by_keyspace_list,
            headers=(
                "keyspace",
                "safetime (UTC)",
                "safetime lag (ms)",
                "safetime skew (ms)",
                "est failover loss (ms)",
            ),
            tablefmt="rounded_grid",
            floatfmt=".3f",
            showindex=False,
        )


def get_status(customer_uuid: str, source_universe_name: str):

    get_source_universe_response = _get_universe_by_name(
        customer_uuid, source_universe_name
    )
    source_universe_details = next(iter(get_source_universe_response), None)
    if source_universe_details is None:
        raise RuntimeError(
            f"ERROR: the universe '{source_universe_name}' was not found."
        )

    else:

        status_list = get_source_xcluster_dr_config(
            customer_uuid, source_universe_name, "all"
        )
        state = status_list["state"]
        status = status_list["status"]
        paused = status_list["paused"]
        primaryUniverseState = status_list["primaryUniverseState"]
        drReplicaUniverseState = status_list["drReplicaUniverseState"]

        with open("config/status.yaml", "r") as file:
            status_tooltips = yaml.safe_load(file)

        configuration_tooltip = status_tooltips.get("configuration", {}).get(
            state, "this is a new status that is undefined"
        )

        replication_tooltip = status_tooltips.get("replication", {}).get(
            status, "this is a new status that is undefined"
        )

        paused_tooltip = status_tooltips.get("paused", {}).get(
            paused, "this is a new status that is undefined"
        )

        source_tooltip = status_tooltips.get("source", {}).get(
            primaryUniverseState,
            "this is a new status that is undefined",
        )

        target_tooltip = status_tooltips.get("target", {}).get(
            drReplicaUniverseState,
            "this is a new status that is undefined",
        )

        print(f"configuration: {state} - {configuration_tooltip}")
        print(f"replication: {status} - {replication_tooltip}")
        print(f"paused? {paused} - {paused_tooltip}")
        print(f"source: {primaryUniverseState} - {source_tooltip}")
        print(f"target: {drReplicaUniverseState} - {target_tooltip}")

        return "Please see the README file for further notes on these status fields."


def get_xcluster_details_by_name(customer_uuid: str, universe_name: str) -> str:
    """
    Helper function to return xCluster details of the universe from a given friendly name.

    :param customer_uuid: str - the customer UUID
    :param universe_name: str - the universe's friendly name
    :raises RuntimeError: if the universe is not found
    """
    universe = next(iter(_get_universe_by_name(customer_uuid, universe_name)), None)

    if universe is None:
        raise RuntimeError(
            f"ERROR: failed to find a universe '{universe_name}' by name"
        )
    else:
        source_config_UUID = universe["drConfigUuidsAsSource"]
        target_config_UUID = universe["drConfigUuidsAsTarget"]

        if len(source_config_UUID) > 0:

            target_uuid_in_this_xcluster_config = _get_xcluster_dr_configs(
                customer_uuid, source_config_UUID[0]
            )["drReplicaUniverseUuid"]

            target_name_in_this_xcluster_config = _get_universe_by_uuid(
                customer_uuid, target_uuid_in_this_xcluster_config
            )["name"]

            print(
                f"{universe_name} universe is a source, and the target universe is: {target_name_in_this_xcluster_config}"
            )

        elif len(target_config_UUID) > 0:

            source_uuid_in_this_xcluster_config = _get_xcluster_dr_configs(
                customer_uuid, target_config_UUID[0]
            )["primaryUniverseUuid"]

            source_name_in_this_xcluster_config = _get_universe_by_uuid(
                customer_uuid, source_uuid_in_this_xcluster_config
            )["name"]

            print(
                f"{universe_name} universe is a target, and the source universe is: {source_name_in_this_xcluster_config}"
            )

        else:

            raise RuntimeError(
                f"ERROR: '{universe_name}' is not configured as part of an xCluster config."
            )
