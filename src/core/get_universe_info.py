from core.internal_rest_apis import _get_universe_by_name


def get_universe_uuid_by_name(customer_uuid: str, universe_name: str) -> str:
    """
    Helper function to return the universeUUID of the Universe from a given friendly name.

    :param customer_uuid: str - the Customer UUID
    :param universe_name: str - the Universe's friendly name
    :return: str - the Universe's UUID
    :raises RuntimeError: if the Universe is not found
    """
    universe = next(iter(_get_universe_by_name(customer_uuid, universe_name)), None)
    if universe is None:
        raise RuntimeError(
            f"ERROR: failed to find a universe '{universe_name}' by name"
        )
    else:
        return universe["universeUUID"]
