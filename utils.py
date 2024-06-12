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

def get_current_and_future_epoch_america_new_york_milliseconds(selected_slot=None):
    tz = pytz.timezone('America/New_York')

    if selected_slot:
        # Parse the selected_slot in EDT timezone and convert to New York timezone
        selected_datetime_edt = datetime.fromisoformat(selected_slot)
        selected_datetime_new_york = selected_datetime_edt.astimezone(tz)
        print(selected_datetime_edt)
        print(selected_datetime_new_york)
        # Calculate one hour before and one hour after the selected slot
        current_datetime = selected_datetime_new_york - timedelta(hours=1)
        future_datetime = selected_datetime_new_york + timedelta(hours=1)
    else:
        current_datetime = datetime.now(tz)
        future_datetime = current_datetime + timedelta(hours=2) 


    print(current_datetime)
    print(future_datetime)
    # Convert both times to epoch timestamps
    # Convert to epoch timestamps and multiply by 1000 to get milliseconds
    current_epoch_ms = int(current_datetime.timestamp()) * 1000
    future_epoch_ms = int(future_datetime.timestamp()) * 1000
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

def get_first_and_third_slots(slots):
    selected_slots = []
    if len(slots) >= 1:
        selected_slots.append(slots[0])
    if len(slots) >= 3:
        selected_slots.append(slots[2])
    return selected_slots