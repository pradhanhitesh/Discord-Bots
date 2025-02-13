from datetime import datetime, timedelta
import pytz
import os
import shutil

def get_date_cycle(upper_range = 1, lower_range=8):
    # Cycle dates every 7 days
    # Helper function for bot-01-phd-alerts.py and Github Action Automation
    now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
    upper = now_ist - timedelta(days=upper_range)
    lower = now_ist - timedelta(days=lower_range)
    upper_str = upper.strftime("%Y/%m/%d")
    lower_str = lower.strftime("%Y/%m/%d")

    return lower_str, upper_str

def delete_data(dir_path="DATA"):
    # Remove all contents but keep the directory
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove files and symlinks
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove directories
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")