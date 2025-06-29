import json
import os

cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(cfg_path, "r") as f:
    config = json.load(f)
