import yaml

from pathlib import Path


def get_demo_config():
    demo_config_file = Path("config/universe.yaml")
    demo_config_data = yaml.safe_load(demo_config_file.read_text())

    XCLUSTER_SOURCE = demo_config_data["XCLUSTER_SOURCE"]
    XCLUSTER_TARGET = demo_config_data["XCLUSTER_TARGET"]
    REPLICATE_DATABASE_NAMES = demo_config_data["REPLICATE_DATABASE_NAMES"]
    TEST_TASK_UUID = demo_config_data["TEST_TASK_UUID"]
    ADD_TABLES_TO_DR_LIST = demo_config_data["ADD_TABLES_TO_DR_LIST"]
    REMOVE_TABLES_FROM_DR_LIST = demo_config_data["REMOVE_TABLES_FROM_DR_LIST"]

    return {
        "XCLUSTER_SOURCE": XCLUSTER_SOURCE,
        "XCLUSTER_TARGET": XCLUSTER_TARGET,
        "REPLICATE_DATABASE_NAMES": REPLICATE_DATABASE_NAMES,
        "TEST_TASK_UUID": TEST_TASK_UUID,
        "ADD_TABLES_TO_DR_LIST": ADD_TABLES_TO_DR_LIST,
        "REMOVE_TABLES_FROM_DR_LIST": REMOVE_TABLES_FROM_DR_LIST,
    }
