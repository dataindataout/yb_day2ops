from core.internal_rest_apis import (
    _get_universe_by_name,
    _get_xcluster_dr_configs,
)


def get_source_xcluster_dr_config(
    customer_uuid: str, source_universe_name: str, key: str
):

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
        elif key != "all":
            return _get_xcluster_dr_configs(customer_uuid, dr_config_source_uuid)[key]
        else:
            return _get_xcluster_dr_configs(customer_uuid, dr_config_source_uuid)
