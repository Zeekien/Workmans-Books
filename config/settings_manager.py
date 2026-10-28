import json
import os

SETTINGS_FILE = "config/settings.json"
DEFAULT_SETTINGS = {
    "developer_mode": False,
    "work_types": {
        "General Maintenance": ["Standard Check", "Cleanup"],
        "Weeding": ["Invasive", "Disposal"],
        "Pruning": ["Haul Away", "Tree Trimming"]
    }
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            updated = False
            if "work_types" not in data:
                data["work_types"] = DEFAULT_SETTINGS["work_types"]
                updated = True
            if "developer_mode" not in data:
                data["developer_mode"] = DEFAULT_SETTINGS["developer_mode"]
                updated = True
            if updated:
                save_settings(data)
            return data
    except Exception:
        return DEFAULT_SETTINGS

def save_settings(settings):
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def get_work_types():
    settings = load_settings()
    return settings.get("work_types", {})

def get_addons_for_work_type(work_type):
    wt = get_work_types()
    return wt.get(work_type, [])

def is_developer_mode():
    settings = load_settings()
    return bool(settings.get("developer_mode", False))