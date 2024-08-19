import yaml

from pathlib import Path


def get_auth_config():
    auth_config_file = Path("config/auth.yaml")
    auth_config_data = yaml.safe_load(auth_config_file.read_text())

    YBA_URL = auth_config_data["YBA_URL"]
    API_HEADERS = {"X-AUTH-YW-API-TOKEN": f"{auth_config_data['API_KEY']}"}

    return {
        "YBA_URL": YBA_URL,
        "API_HEADERS": API_HEADERS,
    }
