from datetime import datetime, timedelta
import pytz

def get_date_cycle(upper_range = 1, lower_range=8):
    # Cycle dates every 7 days
    # Helper function for bot-01-phd-alerts.py and Github Action Automation
    now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
    upper = now_ist - timedelta(days=upper_range)
    lower = now_ist - timedelta(days=lower_range)
    upper_str = upper.strftime("%Y/%m/%d")
    lower_str = lower.strftime("%Y/%m/%d")

    return lower_str, upper_str