import tabulate

from core.internal_rest_apis import (
    _get_configs_by_type,
    _get_universe_by_name,
    _get_database_namespaces,
    _get_xcluster_dr_configs,
    _create_dr_config,
)
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
