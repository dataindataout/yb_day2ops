import os
from pathlib import Path
import pytest
import re
import yaml

from mainapp import get_xcluster_configuration_info

# get testing config values
testing_config_file = Path("config/testing.yaml")
testing_config_data = yaml.safe_load(testing_config_file.read_text())

if testing_config_data:
    for key, value in testing_config_data.items():
        os.environ[key] = str(value)


@pytest.mark.parametrize(
    "key, expected_output",
    [
        ("all", "{'bootstrapParams':"),
        ("paused", "True|False"),
        ("uuid", "'.{8}-.{4}-.{4}-.{4}-.{12}'"),
    ],
)
def test_get_xcluster_configuration_info(capsys, key, expected_output):
    get_xcluster_configuration_info(
        os.environ.get("CUSTOMER_UUID"), os.environ.get("XCLUSTER_SOURCE"), key
    )
    captured = capsys.readouterr()
    assert re.search(expected_output, captured.out) is not None
