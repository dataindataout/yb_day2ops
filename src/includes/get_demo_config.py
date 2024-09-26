import os, yaml

from pathlib import Path


def get_config(file: str):
    config_file = Path(file)
    config_data = yaml.safe_load(config_file.read_text())

    if config_data:
        for key, value in config_data.items():
            os.environ[key] = str(value)
