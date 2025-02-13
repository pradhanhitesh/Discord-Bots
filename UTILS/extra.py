from datetime import datetime, timedelta
import pytz
import os
import shutil
import json

def get_date_cycle(upper_range = 1, lower_range=8):
    # Cycle dates every 7 days
    # Helper function for bot-01-phd-alerts.py and Github Action Automation
    now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
    upper = now_ist - timedelta(days=upper_range)
    lower = now_ist - timedelta(days=lower_range)
    upper_str = upper.strftime("%Y/%m/%d")
    lower_str = lower.strftime("%Y/%m/%d")

    return lower_str, upper_str

def delete_data(dir_path="DATA", keep_file="historical_oped.json"):
    # Iterate through all files and directories in the given path
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        
        # Skip the file that needs to be preserved
        if filename == keep_file:
            continue  # Don't delete this file
        
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove files and symlinks
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove directories
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def load_historical_oped(file_path: str):
    with open(file_path, "r") as file:
        data = json.load(file)
    
    hash_lib = [item for value in data.values() if isinstance(value, list) for item in value]
    return hash_lib

def save_historical_oped(file_path: str, to_save: list):
    # Open and read the JSON file
    with open(file_path, "r") as file:
        data = json.load(file)

    # Add a new key-value pair
    data[str(datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %H:%M'))] = to_save

    # Write back to the file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)