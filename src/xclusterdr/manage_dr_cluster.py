import tabulate

from core.internal_rest_apis import (
    _get_all_ysql_tables_list,
    _get_configs_by_type,
    _get_universe_by_name,
    _get_database_namespaces,
    _get_xcluster_dr_configs,
    _create_dr_config,
    _set_tables_in_dr_config,
)
from core.get_universe_info import get_universe_uuid_by_name
from core.manage_tasks import wait_for_task


def get_source_xcluster_dr_config(customer_uuid: str, source_universe_name: str):

    get_source_universe_response = _get_universe_by_name(
        customer_uuid, source_universe_name
    )
    source_universe_details = next(iter(get_source_universe_response), None)
    if source_universe_details is None:
        raise RuntimeError(
            f"ERROR: the universe '{source_universe_name}' was not found."
        )
    else:
        dr_config_source_uuid = next(
            iter(source_universe_details["drConfigUuidsAsSource"]), None
        )
        if dr_config_source_uuid is None:
            raise RuntimeError(
                f"ERROR: the universe '{source_universe_name}' does not have a DR config."
            )
        else:
            return _get_xcluster_dr_configs(customer_uuid, dr_config_source_uuid)


def get_xcluster_dr_available_tables(
    customer_uuid: str, source_universe_name: str
) -> list:
    """
    For a given universe name, returns a list of database tables not already included in the current xcluster dr config.
    These are the tables that can be added to the configuration. Ideally, these should have sizeBytes = 0 or including
    it will trigger a full backup/restore of the existing database (this will slow the process down).

    :param customer_uuid: str - the customer uuid.
    :param universe_name: str - the name of the universe.
    :return: list<str> - a list of database table ids not already included in the current xCluster DR config.
    """
    universe_uuid = get_universe_uuid_by_name(customer_uuid, source_universe_name)

    all_tables_list = _get_all_ysql_tables_list(customer_uuid, universe_uuid)

    xcluster_dr_existing_tables_id = get_source_xcluster_dr_config(
        customer_uuid, source_universe_name
    )["tables"]

    # filter out any tables whose ids are not already in the current xcluster dr config
    # additionally filter out index tables,
    # which do not need to be added separately from their enclosing table
    unreplicated_tables_list = [
        t
        for t in all_tables_list
        if t["tableID"] not in xcluster_dr_existing_tables_id
        and t["isIndexTable"] is not True
    ]

    formatted_unreplicated_tables_list = []
    for i in unreplicated_tables_list:
        new_row = [
            i["tableID"],
            i["pgSchemaName"],
            i["keySpace"],
            i["tableName"],
            i["sizeBytes"],
        ]
        formatted_unreplicated_tables_list.append(new_row)

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
        formatted_unreplicated_tables_list,
        headers=("id", "schema", "keyspace", "table", "size (bytes)"),
        tablefmt="rounded_grid",
        floatfmt=".0f",
        showindex=False,
    )


def create_xcluster_dr(
    customer_uuid: str,
    source_universe_name: str,
    target_universe_name: str,
    db_names: set,
):

    storage_configs = _get_configs_by_type(customer_uuid, "STORAGE")

    if len(storage_configs) < 1:
        raise RuntimeError(
            "WARN: no storage configs found, at least one is required for xCluster DR setup!"
        )

    storage_config_uuid = storage_configs[1]["configUUID"]

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

    target_universe_response = _get_universe_by_name(
        customer_uuid, target_universe_name
    )
    target_universe_details = next(iter(target_universe_response), None)

    if target_universe_details is None:
        raise RuntimeError(
            f"ERROR: the target universe '{target_universe_name}' was not found"
        )

    target_universe_uuid = target_universe_details["universeUUID"]

    dbs_list = _get_database_namespaces(customer_uuid, source_universe_uuid)
    dbs_list_uuids = [d["namespaceUUID"] for d in dbs_list if d["name"] in db_names]

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
        customer_uuid, source_universe_name
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
