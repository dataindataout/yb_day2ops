import tabulate

import datetime
import pytz

from core.internal_rest_apis import (
    _get_xcluster_dr_safetime,
    _get_universe_by_name,
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

        print("configuration: " + status_list["state"])
        print("replication: " + status_list["status"])
        print("paused? " + str(status_list["paused"]))
        print("source: " + status_list["primaryUniverseState"])
        print("target: " + status_list["drReplicaUniverseState"])
        return "Please see the README file for interpretation of these results."
