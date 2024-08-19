import requests
import time

from core.internal_rest_apis import _get_task_status
from includes.get_auth_config import get_auth_config

auth_config = get_auth_config()


def wait_for_task(
    customer_uuid: str, task_response, friendly_name="UNKNOWN", sleep_interval=2
):
    """
    Utility function that waits for a given task to complete and updates the console every sleep interval.

    On success the return will be final task status.

    See also:
     - https://api-docs.yugabyte.com/docs/yugabyte-platform/08618836e48aa-customer-task-data

    :param customer_uuid: str - the customer UUID
    :param task_response: json<ActionResponse> - the task response body (json) from the action
    :param friendly_name: str - a friendly task name to display in output (optional, default is UNKNOWN)
    :param sleep_interval: int - an interval to sleep while task is running (optional, default 15s)
    :return: json of CustomerTaskData (the final task result)
    :raises RuntimeError: if the task fails or cannot be found
    """
    if "taskUUID" not in task_response:
        raise RuntimeError(
            f"ERROR: failed to process '{friendly_name}' no taskUUID {task_response}"
        )

    task_uuid = task_response["taskUUID"]

    while True:
        task_status = _get_task_status(customer_uuid, task_uuid)
        match task_status["status"]:
            case "Success":
                print(f"Task '{friendly_name}': {task_uuid} finished successfully!")
                return task_status
            case "Failure":
                failure_message = f"Task '{friendly_name}': {task_uuid} failed, but could not get the failure messages"
                action_failed_response = requests.get(
                    url=f"{auth_config['YBA_URL']}/api/customers/{customer_uuid}/tasks/{task_uuid}/failed",
                    headers=auth_config["API_HEADERS"],
                ).json()
                if "failedSubTasks" in action_failed_response:
                    errors = [
                        subtask["errorString"]
                        for subtask in action_failed_response["failedSubTasks"]
                    ]
                    failure_message = (
                        f"Task '{friendly_name}': {task_uuid} failed with the following errors: "
                        + "\n".join(errors)
                    )

                raise RuntimeError(failure_message)
            case _:
                print(
                    f"Waiting for '{friendly_name}' (task='{task_uuid}'): {task_status['percent']:.0f}% complete..."
                )
                time.sleep(sleep_interval)
