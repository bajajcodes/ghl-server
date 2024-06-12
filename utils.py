from datetime import datetime, timedelta

import pytz


def get_current_date_america_new_york():
    tz = pytz.timezone('America/New_York')
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")

def get_current_time_america_new_york():
    tz = pytz.timezone('America/New_York')
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")

def get_current_and_future_epoch_america_new_york_milliseconds():
    tz = pytz.timezone('America/New_York')
    now = datetime.now(tz)
    print(now)
    # Calculate future time (2 hours from now)
    future_time = now + timedelta(hours=2)
    print(future_time)
    # Convert both times to epoch timestamps
    # Convert to epoch timestamps and multiply by 1000 to get milliseconds
    current_epoch_ms = int(now.timestamp()) * 1000
    future_epoch_ms = int(future_time.timestamp()) * 1000
    print(current_epoch_ms)
    print(future_epoch_ms)
    return current_epoch_ms, future_epoch_ms

def extract_two_slots(response_data):
    today = datetime.now().strftime("%Y-%m-%d")  # Get today's date in YYYY-MM-DD format
    slots = response_data.get(today, {}).get("slots", [])

    return slots[:2]  # Return the first two slots (or fewer if there aren't enough)

def replace_placeholders(prompt, now, user_response):
    prompt = prompt.replace("{{now}}", now)
    prompt = prompt.replace("{{user_response}}", user_response)
    return prompt
