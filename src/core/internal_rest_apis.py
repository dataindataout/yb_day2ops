import json
import requests

from includes.get_auth_config import get_auth_config

auth_config = get_auth_config()


def _get_universe_by_name(customer_uuid: str, universe_name: str):
    """
    Basic function that returns a universe by its friendly name.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/66e50c174046d-list-universes
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/8682dd63e9165-universe-resp

    :param customer_uuid: str - the customer UUID
    :param universe_name: str - the friendly name of the universe to be returned
    :return: json array of UniverseResp
    """
    return requests.get(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/universes?name={universe_name}",
        headers=auth_config["API_HEADERS"],
    ).json()


def _get_database_namespaces(
    customer_uuid: str,
    universe_uuid: str,
    table_type="PGSQL_TABLE_TYPE",
) -> list:
    """
    Returns a list of database "namespaces" (database names) filtered by a given type. For xCluster DR this will be
    PGSQL_TABLE_TYPE (which is the default).

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/bc7e19ff7baec-list-all-namespaces
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/f0d617b52337d-namespace-info-resp

    :param customer_uuid: str - the Customer UUID
    :param universe_uuid: str - the Universe UUID
    :param table_type: str - the type of namespaces to return (e.g. YQL_TABLE_TYPE, REDIS_TABLE_TYPE, PGSQL_TABLE_TYPE,
     TRANSACTION_STATUS_TABLE_TYPE).
    :return: json array of NamespaceInfoResp
    """
    response = requests.get(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/universes/{universe_uuid}/namespaces",
        headers=auth_config["API_HEADERS"],
    ).json()
    return list(filter(lambda db: db["tableType"] == table_type, response))


def _get_session_info():
    """
    Basic function that gets the current user's session info from YBA. Primarily use this as a convenient way to get
    the current user's `customerUUID`.

    See also: https://api-docs.yugabyte.com/docs/yugabyte-platform/3b0b8530951e6-get-current-user-customer-uuid-auth-api-token

    :return: json of SessionInfo
    """
    return requests.get(
        url=f"{auth_config['YBA_URL']}/api/v1/session_info",
        headers=auth_config["API_HEADERS"],
    ).json()


def _get_configs_by_type(customer_uuid: str, config_type: str):
    """
    Return a Customer's configs of a specific config type. This is useful for getting things like the STORAGE configs.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/d09c43e4a8bfd-list-all-customer-configurations
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/0e51caecbdf07-customer-config

    :param customer_uuid: str - the customer UUID
    :param config_type: enum<str> - the config type (of STORAGE, ALERTS, CALLHOME, PASSWORD_POLICY).
    :return: json array of CustomerConfig
    """
    response = requests.get(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/configs",
        headers=auth_config["API_HEADERS"],
    ).json()
    return list(filter(lambda config: config["type"] == config_type, response))


def _get_task_status(customer_uuid: str, task_uuid: str) -> json:
    """
    Basic function that gets a task's status for a given task UUID in YBA.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/ae83717943b4c-get-a-task-s-status
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/08618836e48aa-customer-task-data

    :param customer_uuid: str - the customer UUID
    :param task_uuid: str - the task's UUID
    :return: json<CustomerTaskData>
    """
    return requests.get(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/tasks/{task_uuid}",
        headers=auth_config["API_HEADERS"],
    ).json()


def _get_all_ysql_tables_list(
    customer_uuid: str,
    universe_uuid: str,
    table_type="PGSQL_TABLE_TYPE",
    include_parent_table_info=False,
    only_supported_for_xcluster=True,
    dbs_include_list=None,
):
    """
    Returns a list of YSQL tables for a given Universe possibly filtered by type and if it is supported by xCluster.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/d00ca6d91e3aa-list-all-tables
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/2419074f53925-table-info-resp

    :param customer_uuid: str - the Customer UUID
    :param universe_uuid: str - the Universe UUID
    :param table_type: str - the type of tables to return
    :param include_parent_table_info: bool - whether to include the parent table information
    :param only_supported_for_xcluster: bool - whether to only include XCluster tables
    :param dbs_include_list: list<str> - list of database names to include (filter out any not matching); default None
    :return: json array of TableInfoResp (possibly filtered)
    """
    response = requests.get(
        url=(
            f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/universes/{universe_uuid}/tables"
            f"?includeParentTableInfo={str(include_parent_table_info).lower()}"
            f"&onlySupportedForXCluster={str(only_supported_for_xcluster).lower()}"
        ),
        headers=auth_config["API_HEADERS"],
    ).json()

    if dbs_include_list is None:
        return list(filter(lambda t: t["tableType"] == table_type, response))
    else:
        return list(
            filter(
                lambda t: t["tableType"] == table_type
                and t["keySpace"] in dbs_include_list,
                response,
            )
        )


def _get_xcluster_configs(customer_uuid, xcluster_config_uuid):
    """
    Basic function that gets the xCluster configration data for a given xCluster config UUID from YBA.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/3ff7ead3de133-get-xcluster-config
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/1486cbdec4522-x-cluster-config-get-resp

    :param customer_uuid: str - the customer UUID
    :param xcluster_config_uuid: str - the xCluster Config UUID
    :return: json of XClusterConfigGetResp
    """
    return requests.get(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/xcluster_configs/{xcluster_config_uuid}",
        headers=auth_config["API_HEADERS"],
    ).json()


def _get_xcluster_dr_configs(customer_uuid: str, xcluster_dr_uuid: str) -> json:
    """
    Basic function that gets an xCluster DR configuration for a given DR config UUID.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/branches/2.20/2963c1edbb9e9-get-disaster-recovery-config
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/branches/2.20/db4d138705705-dr-config

    :param customer_uuid: str - the customer UUID
    :param xcluster_dr_uuid: str - the DR config UUID to return
    :return: json of DrConfig
    """
    return requests.get(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/dr_configs/{xcluster_dr_uuid}",
        headers=auth_config["API_HEADERS"],
    ).json()


def _create_dr_config(
    customer_uuid: str,
    storage_config_uuid: str,
    source_universe_uuid: str,
    target_universe_uuid: str,
    dbs_include_list=None,
    parallelism=8,
):
    """
    Creates a new xCluster DR config for given source and target universe and a required storage config.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/branches/2.20/d8cf017de217e-create-disaster-recovery-config
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/64d854c13e51b-ybp-task

    :param customer_uuid: str - the Customer UUID
    :param storage_config_uuid: str - a storage config for backup/restore of data from source to target
    :param source_universe_uuid: str - the source Universe UUID
    :param target_universe_uuid: str - the target Universe UUID
    :param dbs_include_list: list<str> - list of database names to include (filter out any not matching); default None
    :param parallelism: int - the number of parallel threads to use during backup/restore bootstrap; default 8
    :param dry_run: bool - whether to perform as a "dry run"; default False
    :return: json of YBPTask (it may be passed to wait_for_task)
    """
    disaster_recovery_create_form_data = {
        "bootstrapParams": {
            "backupRequestParams": {
                "parallelism": parallelism,
                "storageConfigUUID": storage_config_uuid,
            }
        },
        "dbs": dbs_include_list,
        "name": f"DR-config-{source_universe_uuid}-to-{target_universe_uuid}",
        "sourceUniverseUUID": source_universe_uuid,
        "targetUniverseUUID": target_universe_uuid,
    }

    return requests.post(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/dr_configs",
        json=disaster_recovery_create_form_data,
        headers=auth_config["API_HEADERS"],
    ).json()


def _set_tables_in_dr_config(
    customer_uuid: str,
    dr_config_uuid: str,
    storage_config_uuid: str,
    tables_include_set=None,
    auto_include_indexes=True,
    parallelism=8,
):
    """
    Updates the set of tables that are included in the xCluster DR. As this is a POST operation, the tables list should
    always contain the full set of table IDs intended to be used in xCluster DR replication. This also means that to
    effectively remove tables, the POST should contain the existing set of tables minus the tables to be removed.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/branches/2.20/570cb66189f0d-set-tables-in-disaster-recovery-config
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/64d854c13e51b-ybp-task

    :param customer_uuid: str - the Customer UUID
    :param dr_config_uuid: str - the DR config UUID to use
    :param storage_config_uuid: str - a storage config UUID for backup/restore of data
    :param tables_include_set: set<str> - list of table UUIDs to include in replication
    :param auto_include_indexes: bool - whether to automatically include indexes of the selected tables; default True
    :param parallelism: int - the number of parallel threads to use during backup/restore bootstrap; default 8
    :return: json of YBPTask (it may be passed to wait_for_task)
    """
    disaster_recovery_set_tables_form_data = {
        "autoIncludeIndexTables": auto_include_indexes,
        "bootstrapParams": {
            "backupRequestParams": {
                "parallelism": parallelism,
                "storageConfigUUID": storage_config_uuid,
            }
        },
        "tables": tables_include_set,
    }

    return requests.post(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/dr_configs/{dr_config_uuid}/set_tables",
        json=disaster_recovery_set_tables_form_data,
        headers=auth_config["API_HEADERS"],
    ).json()


def _pause_xcluster_config(customer_uuid: str, xcluster_config_uuid: str):
    """
    Pauses the underlying xCluster replication.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/3d17ffa45a16e-edit-xcluster-config
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/64d854c13e51b-ybp-task

    :param customer_uuid: str - the Customer UUID
    :param xcluster_config_uuid: str - the xCluster config UUID to pause
    :return: json of YBPTask (it may be passed to wait_for_task)
    """
    xcluster_replication_edit_form_data = {"status": "Paused"}
    return requests.put(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/xcluster_configs/{xcluster_config_uuid}",
        json=xcluster_replication_edit_form_data,
        headers=auth_config["API_HEADERS"],
    ).json()


def _resume_xcluster_config(customer_uuid: str, xcluster_config_uuid: str):
    """
    Resumes the underlying xCluster replication.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/3d17ffa45a16e-edit-xcluster-config
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/64d854c13e51b-ybp-task

    :param customer_uuid: str - the Customer UUID
    :param xcluster_config_uuid: str - the xCluster config UUID to resume
    :return: json of YBPTask (it may be passed to wait_for_task)
    """
    xcluster_replication_edit_form_data = {"status": "Running"}
    return requests.put(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/xcluster_configs/{xcluster_config_uuid}",
        json=xcluster_replication_edit_form_data,
        headers=auth_config["API_HEADERS"],
    ).json()


def _switchover_xcluster_dr(
    customer_uuid: str,
    dr_config_uuid: str,
    primary_universe_uuid: str,
    dr_replica_universe_uuid: str,
):
    """
    Initiates an xCluster DR planned switchover.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/branches/2.20/066dda1e654a3-switchover-a-disaster-recovery-config
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/64d854c13e51b-ybp-task

    :param customer_uuid: str - the Customer UUID
    :param dr_config_uuid: str - the DR config UUID to use
    :param primary_universe_uuid: str - the primary Universe UUID
    :param dr_replica_universe_uuid: str - the secondary (replica) Universe UUID
    :return: json of YBPTask (it may be passed to wait_for_task)
    """
    disaster_recovery_switchover_form_data = {
        "primaryUniverseUuid": primary_universe_uuid,
        "drReplicaUniverseUuid": dr_replica_universe_uuid,
    }

    return requests.post(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/dr_configs/{dr_config_uuid}/switchover",
        json=disaster_recovery_switchover_form_data,
        headers=auth_config["API_HEADERS"],
    ).json()


def _failover_xcluster_dr(
    customer_uuid: str,
    dr_config_uuid: str,
    primary_universe_uuid: str,
    dr_replica_universe_uuid: str,
    namespace_id_safetime_epoch_us_map: dict,
):
    """
    Initiates an xCluster DR fail-over after an "unplanned" failure of the Primary cluster/region.

    NOTE: it is anticipated that, in this failure scenario, it may first require an HA switchover of YBA itself before being able to run this operation. This may also require changing the underlying YBA_URL used if the HA instance is not already behind a load balancer.

    After this operation is successful, the DR Replica becomes the new Primary cluster without an automatic DR
    configuration. Once the Primary has recovered and is accessible again, run the Restart (Repair) xCluster DR
    operations and, once completed, optionally do a DR Switchover to return back to the original Primary DR.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/branches/2.20/a3bcb16787481-failover-a-disaster-recovery-config

    :param customer_uuid: str - the Customer UUID
    :param dr_config_uuid: str - the DR config UUID to use
    :param primary_universe_uuid: str - the primary Universe UUID
    :param dr_replica_universe_uuid: str - the secondary (replica) Universe UUID
    :param namespace_id_safetime_epoch_us_map: dict<str, int> - the current epoch safetimes for the DR config
    :return: json of YBPTask (it may be passed to wait_for_task)
    """
    disaster_recovery_failover_form_data = {
        "primaryUniverseUuid": primary_universe_uuid,
        "drReplicaUniverseUuid": dr_replica_universe_uuid,
        "namespaceIdSafetimeEpochUsMap": namespace_id_safetime_epoch_us_map,
    }
    # pprint(disaster_recovery_failover_form_data)
    return requests.post(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/dr_configs/{dr_config_uuid}/failover",
        json=disaster_recovery_failover_form_data,
        headers=auth_config["API_HEADERS"],
    ).json()


def _get_xcluster_dr_safetime(customer_uuid: str, dr_config_uuid: str):
    """
    Get the xCluster DR config safe times. This information is needed to pass into the _failover_xcluster_dr method.

    See also:
     - <can't find these docs yet>

    :param customer_uuid: str - the Customer UUID
    :param dr_config_uuid: str - the DR config UUID to use
    :return: json<DrConfigSafeTimeResp>
    """
    return requests.get(
        url=f"{auth_config['YBA_URL']}/api/v1/customers/{customer_uuid}/dr_configs/{dr_config_uuid}/safetime",
        headers=auth_config["API_HEADERS"],
    ).json()
