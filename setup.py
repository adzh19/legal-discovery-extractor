import os
import json
import time
from dotenv import load_dotenv, find_dotenv
from box_client import get_box_client

# ----------------------------
# Environment Setup
# ----------------------------

env_path = find_dotenv()
load_dotenv(env_path)

DEV_TOKEN = os.getenv("DEVELOPER_TOKEN")

if not DEV_TOKEN:
    raise ValueError("Developer token not found in environment variables!")

client = get_box_client(DEV_TOKEN)

ROOT_FOLDER_ID = os.getenv("ROOT_FOLDER_ID" , "0")

SUBFOLDER_NAMES = [
    "4) Json",
    "3) Approved Excels",
    "2) Pending Excels",
    "1) Reports",
]

EXPECTED_KEYS = [
    "ROOT_FOLDER_ID",
    "REPORTS_FOLDER_ID",
    "PENDING_EXCELS_FOLDER_ID",
    "APPROVED_EXCELS_FOLDER_ID",
    "JSON_FOLDER_ID",
]

JSON_STORE_FILE = "box_folders.json"

# ----------------------------
# JSON Utilities
# ----------------------------

def load_json_store():
    if os.path.exists(JSON_STORE_FILE):
        with open(JSON_STORE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_json_store(data):
    with open(JSON_STORE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def project_is_fully_configured(data, project_name):
    if project_name not in data:
        return False
    for key in EXPECTED_KEYS:
        if key not in data[project_name]:
            return False
    return True

# ----------------------------
# Folder Utilities
# ----------------------------

def get_or_create_main_folder(root_id, folder_name):
    print(f"\n🔍 Searching for main folder '{folder_name}'...")
    items = client.folders.get_folder_items(root_id).entries

    for item in items:
        if item.type == "folder" and item.name.lower() == folder_name.lower():
            print(f"✅ Found existing main folder (ID: {item.id})")
            return item.id

    folder = client.folders.create_folder(folder_name, parent={"id": root_id})
    print(f"🆕 Created main folder (ID: {folder.id})")
    return folder.id

def get_or_create_subfolders(parent_folder_id):
    print("\n🔍 Checking subfolders...")
    existing_items = client.folders.get_folder_items(parent_folder_id).entries
    existing_subfolders = {
        item.name.lower(): item.id
        for item in existing_items
        if item.type == "folder"
    }

    subfolders = {}
    for name in SUBFOLDER_NAMES:
        name_lower = name.lower()
        if name_lower in existing_subfolders:
            subfolders[name] = existing_subfolders[name_lower]
            print(f"📂 Exists: '{name}'")
        else:
            folder = client.folders.create_folder(name, parent={"id": parent_folder_id})
            subfolders[name] = folder.id
            print(f"🆕 Created: '{name}'")
            time.sleep(1)
    return subfolders

# ----------------------------
# Main Script
# ----------------------------

if __name__ == "__main__":
    dashboard_name = input("\nEnter the name of the dashboard folder: ").strip()
    if not dashboard_name:
        raise ValueError("Dashboard folder name cannot be empty.")

    data = load_json_store()

    # 🚀 Fast path — everything already configured
    if project_is_fully_configured(data, dashboard_name):
        print("✅ Dashboard already fully configured. Skipping folder checks.")
        print("🎉 Done.")
        exit()

    # Otherwise, we need to verify/create folders
    root_folder_id = get_or_create_main_folder(ROOT_FOLDER_ID, dashboard_name)
    subfolders = get_or_create_subfolders(root_folder_id)

    new_structure = {
        "ROOT_FOLDER_ID": root_folder_id,
        "REPORTS_FOLDER_ID": subfolders["1) Reports"],
        "PENDING_EXCELS_FOLDER_ID": subfolders["2) Pending Excels"],
        "APPROVED_EXCELS_FOLDER_ID": subfolders["3) Approved Excels"],
        "JSON_FOLDER_ID": subfolders["4) Json"],
    }

    changed = False
    if dashboard_name not in data:
        data[dashboard_name] = new_structure
        changed = True
        print("🆕 Added new project to JSON.")
    else:
        for key, value in new_structure.items():
            if key not in data[dashboard_name]:
                data[dashboard_name][key] = value
                changed = True
                print(f"➕ Added missing field: {key}")

    if changed:
        save_json_store(data)
        print("✅ JSON updated.")
    else:
        print("✅ JSON already up to date.")

    print("🎉 Done.")