# utils/config_loader.py
import json
import os
from config import CONFIG

def load_config_data(filename="config_data.json"):
    data_path = CONFIG.get("DATA_PATH", "data")
    filepath = os.path.join(data_path, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
