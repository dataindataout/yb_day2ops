import tabulate

from core.internal_rest_apis import (
    _get_all_ysql_tables_list,
    _get_universe_by_name,
    _get_database_namespaces,
    _get_xcluster_dr_configs,
    _get_universe_by_uuid,
    _create_dr_config,
    _delete_xcluster_dr_config,
    _set_tables_in_dr_config,
    _pause_xcluster_config,
    _resume_xcluster_config,
    _switchover_xcluster_dr,
    _failover_xcluster_dr,
    _get_xcluster_dr_safetime,
    _recover_xcluster_dr_config,
    _get_backup_UUID_by_name,
)
from core.get_universe_info import get_universe_uuid_by_name
from core.manage_tasks import wait_for_task
from xclusterdr.common import get_source_xcluster_dr_config


def get_xcluster_tables(customer_uuid: str, source_universe_name: str) -> list:
    """
    For a given universe name, returns a list of database tables included or not included in the current xcluster dr config. An indicator shows the tables that can be added to the configuration. Ideally, the tables added should have sizeBytes = 0 or it will trigger a full backup/restore of the existing database (this will slow the process down).

    :param customer_uuid: str - the customer uuid.
    :param universe_name: str - the name of the universe.
    :return: list<str> - a list of database table ids not already included in the current xCluster DR config.
    """
    universe_uuid = get_universe_uuid_by_name(customer_uuid, source_universe_name)

    all_tables_list = sorted(
        _get_all_ysql_tables_list(customer_uuid, universe_uuid),
        key=lambda t: (t["keySpace"], t["tableName"]),
    )

    xcluster_dr_existing_tables_id = get_source_xcluster_dr_config(
        customer_uuid, source_universe_name, "tables"
    )

    formatted_tables_list = []
    for table in all_tables_list:
        if not table["isIndexTable"]:
            replicated = (
                "Yes" if table["tableID"] in xcluster_dr_existing_tables_id else ""
            )
            new_row = [
                replicated,
                table["pgSchemaName"],
                table["keySpace"],
                table["tableName"],
                table["sizeBytes"],
                table["tableID"],
            ]
            formatted_tables_list.append(new_row)

    print(
        "You can use the do-add-tables-to-dr command to add these to the xCluster DR configuration by table id."
    )

    print(
        "NOTE 1: Be sure that the table definition exists on the source and target, and that the table is empty."
    )

    print(
        "NOTE 2: When adding tables, all new tables within a keyspace must be added at once."
    )

    return tabulate.tabulate(
        formatted_tables_list,
        headers=("replicated?", "schema", "keyspace", "table", "size (bytes)", "id"),
        tablefmt="rounded_grid",
        floatfmt=".0f",
        showindex=False,
    )


def create_xcluster_dr(
    customer_uuid: str,
    source_universe_name: str,
    target_universe_name: str,
    db_names: list,
    backup_location: str,
):

    # verify the storage location

    storage_configs = _get_backup_UUID_by_name(customer_uuid, backup_location)
    if len(storage_configs) < 1:
        raise RuntimeError(
            f"ERROR: The backup location '{backup_location}' was not found"
        )

    else:
        storage_config_uuid = storage_configs[0]["configUUID"]

    # verify the source universe

    get_source_universe_response = _get_universe_by_name(
        customer_uuid, source_universe_name
    )
    source_universe_details = next(iter(get_source_universe_response), None)
    if source_universe_details is None:
        raise RuntimeError(
            f"ERROR: the universe '{source_universe_name}' was not found"
        )

    source_universe_uuid = source_universe_details["universeUUID"]

    dr_config_source_uuid = next(
        iter(source_universe_details["drConfigUuidsAsSource"]), None
    )
    # see note below about prechecks in dry run
    if dr_config_source_uuid is not None:
        # dr_config = get_dr_configs(session_uuid, dr_config_source_uuid)
        raise RuntimeError(
            f"WARN: the source universe '{source_universe_name}' already has a disaster-recovery config:"
            f" {dr_config_source_uuid},"
        )

    # verify the target universe

    target_universe_response = _get_universe_by_name(
        customer_uuid, target_universe_name
    )
    target_universe_details = next(iter(target_universe_response), None)

    if target_universe_details is None:
        raise RuntimeError(
            f"ERROR: the target universe '{target_universe_name}' was not found"
        )

    target_universe_uuid = target_universe_details["universeUUID"]

    # verify the list of databases

    dbs_list = _get_database_namespaces(customer_uuid, source_universe_uuid)
    dbs_list_uuids = [d["namespaceUUID"] for d in dbs_list if d["name"] in db_names]

    # call the api request

    create_dr_response = _create_dr_config(
        customer_uuid,
        storage_config_uuid,
        source_universe_uuid,
        target_universe_uuid,
        dbs_list_uuids,
    )

    wait_for_task(customer_uuid, create_dr_response, "Create xCluster DR")

    dr_config_uuid = create_dr_response["resourceUUID"]
    print(f"SUCCESS: created disaster-recovery config {dr_config_uuid}")
    return dr_config_uuid


def delete_xcluster_dr(customer_uuid, source_universe_name) -> str:
    """
    Delete an xCluster DR configuration.

    :param customer_uuid: str - the customer uuid
    :param source_universe_name: str - the name of the source universe
    :return:
    """
    get_universe_response = _get_universe_by_name(customer_uuid, source_universe_name)
    universe_details = next(iter(get_universe_response), None)
    if universe_details is None:
        raise RuntimeError(
            f"ERROR: source universe '{source_universe_name}' was not found!"
        )

    dr_config_source_uuid = next(iter(universe_details["drConfigUuidsAsSource"]), None)
    if dr_config_source_uuid is None:
        raise RuntimeError(
            f"ERROR: the universe '{source_universe_name}' is not the source in a disaster-recovery config"
        )

    response = _delete_xcluster_dr_config(customer_uuid, dr_config_source_uuid)
    dr_config_uuid = wait_for_task(customer_uuid, response, "Delete xCluster DR")
    print(f"SUCCESS: deleted disaster-recovery config '{response['resourceUUID']}'.")
    return dr_config_uuid


def add_tables_to_xcluster_dr(
    customer_uuid: str, source_universe_name: str, add_table_ids: list
) -> str:
    """
    Adds a set of tables to replication in an existing xCluster DR config.

    See also: https://api-docs.yugabyte.com/docs/yugabyte-platform/branches/2.20/570cb66189f0d-set-tables-in-disaster-recovery-config

    :param customer_uuid: str - the customer uuid
    :param source_universe_name: str - the name of the source universe
    :param add_tables_ids: set<str> - a set of table ids to add to replication
    :return: str - a resource uuid
    :raises RuntimeError: if no tables could be found to add to the xCluster DR config
    """
    xcluster_dr_config = get_source_xcluster_dr_config(
        customer_uuid, source_universe_name, "all"
    )
    xcluster_dr_uuid = xcluster_dr_config["uuid"]
    storage_config_uuid = xcluster_dr_config["bootstrapParams"]["backupRequestParams"][
        "storageConfigUUID"
    ]

    merged_dr_tables_list = xcluster_dr_config["tables"] + add_table_ids

    resp = _set_tables_in_dr_config(
        customer_uuid, xcluster_dr_uuid, storage_config_uuid, merged_dr_tables_list
    )
    return wait_for_task(customer_uuid, resp, "Add tables to xCluster DR")


def pause_xcluster(customer_uuid, xcluster_source_name):
    dr_config = get_source_xcluster_dr_config(
        customer_uuid, xcluster_source_name, "all"
    )
    resp = _pause_xcluster_config(customer_uuid, dr_config["xclusterConfigUuid"])
    wait_for_task(customer_uuid, resp, "Pause XCluster")
    print("Replication is paused? ")
    print(get_source_xcluster_dr_config(customer_uuid, xcluster_source_name, "paused"))


def resume_xcluster(customer_uuid, xcluster_source_name):
    dr_config = get_source_xcluster_dr_config(
        customer_uuid, xcluster_source_name, "all"
    )
    resp = _resume_xcluster_config(customer_uuid, dr_config["xclusterConfigUuid"])
    wait_for_task(customer_uuid, resp, "Resume XCluster")
    print("Replication is paused? ")
    print(get_source_xcluster_dr_config(customer_uuid, xcluster_source_name, "paused"))


def perform_xcluster_dr_switchover(
    customer_uuid: str,
    source_universe_name: str,
) -> str:
    """
    Performs an xCluster DR switchover (a planned switchover).  This effectively changes the direction of the xCluster replication with zero RPO.

    :param customer_uuid: str - the customer uuid
    :param source_universe_name: str - the name of the source universe
    :return: resource_uuid: str - the uuid of the resource being removed
    """
    dr_config = get_source_xcluster_dr_config(
        customer_uuid, source_universe_name, "all"
    )
    dr_config_uuid = dr_config["uuid"]
    primary_universe_uuid = dr_config["primaryUniverseUuid"]
    dr_replica_universe_uuid = dr_config["drReplicaUniverseUuid"]

    resp = _switchover_xcluster_dr(
        customer_uuid, dr_config_uuid, primary_universe_uuid, dr_replica_universe_uuid
    )
    return wait_for_task(customer_uuid, resp, "Switchover XCluster DR")


def perform_xcluster_dr_failover(customer_uuid: str, source_universe_name: str) -> str:
    """
    Performs an xCluster DR failover (unplanned emergency). This promotes the DR replica to be the Primary. This operation has a small, but non-zero RPO.

    :param customer_uuid: str - the customer uuid
    :param source_universe_name: str - the name of the source universe
    :return: resource_uuid: str - the uuid of the resource being failed over to?
    """
    dr_config = get_source_xcluster_dr_config(
        customer_uuid, source_universe_name, "all"
    )

    dr_config_uuid = dr_config["uuid"]
    primary_universe_uuid = dr_config["primaryUniverseUuid"]
    dr_replica_universe_uuid = dr_config["drReplicaUniverseUuid"]

    xcluster_dr_safetimes = _get_xcluster_dr_safetime(customer_uuid, dr_config_uuid)

    safetime_epoch_map = {
        entry["namespaceId"]: entry["safetimeEpochUs"]
        for entry in xcluster_dr_safetimes["safetimes"]
    }

    resp = _failover_xcluster_dr(
        customer_uuid,
        dr_config_uuid,
        primary_universe_uuid,
        dr_replica_universe_uuid,
        safetime_epoch_map,
    )
    return wait_for_task(customer_uuid, resp, "Failover XCluster DR")


def perform_xcluster_dr_recovery(customer_uuid: str, source_universe_name: str) -> str:
    """
    Performs an xCluster DR recovery after an unplanned failover.

    This operation currently assumes that the user's intent is to reuse the original Primary (the failed) cluster as the new DR Replica. This operation will trigger a full bootstrap of the current Primary and restores it to the old Primary. The time to run this command is based on the size of the database(s) being restored.

    :param customer_uuid: str - the customer uuid
    :param source_universe_name: str - the name of the source universe
    :return: resource_uuid: str - the uuid of the resource being recovered
    """
    dr_config = get_source_xcluster_dr_config(
        customer_uuid, source_universe_name, "all"
    )

    dr_config_uuid = dr_config["uuid"]

    resp = _recover_xcluster_dr_config(customer_uuid, dr_config_uuid)
    return wait_for_task(customer_uuid, resp, "Recover XCluster DR")


def get_xcluster_details_by_name(customer_uuid: str, universe_name: str) -> str:
    """
    Helper function to return the source given any universe name.
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
            # target_uuid_in_this_xcluster_config = _get_xcluster_dr_configs(
            #     customer_uuid, source_config_UUID[0]
            # )["drReplicaUniverseUuid"]
            # target_name_in_this_xcluster_config = _get_universe_by_uuid(
            #     customer_uuid, target_uuid_in_this_xcluster_config
            # )["name"]
            print(f"{universe_name}")
        elif len(target_config_UUID) > 0:
            source_uuid_in_this_xcluster_config = _get_xcluster_dr_configs(
                customer_uuid, target_config_UUID[0]
            )["primaryUniverseUuid"]
            source_name_in_this_xcluster_config = _get_universe_by_uuid(
                customer_uuid, source_uuid_in_this_xcluster_config
            )["name"]
            print(f"{source_name_in_this_xcluster_config}")
        else:
            raise RuntimeError(
                f"ERROR: '{universe_name}' is not configured as part of an xCluster config."
            )
