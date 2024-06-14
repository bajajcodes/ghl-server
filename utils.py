from datetime import datetime, timedelta

import pytz


def get_current_date_america_new_york():
    tz = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")


def get_current_time_america_new_york():
    tz = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")


def is_outside_business_hours():
    tz = pytz.timezone("America/New_York")
    now = datetime.now(tz)

    # Convert the current time to epoch timestamp
    current_epoch_ms = int(now.timestamp()) * 1000

    # Set the start and end time for business hours
    start_time = datetime(now.year, now.month, now.day, 8, 0, 0, tzinfo=tz)
    end_time = datetime(now.year, now.month, now.day, 17, 0, 0, tzinfo=tz)

    # Convert the start and end time to epoch timestamps
    start_epoch_ms = int(start_time.timestamp()) * 1000
    end_epoch_ms = int(end_time.timestamp()) * 1000

    # Check if the current time is outside business hours
    return current_epoch_ms < start_epoch_ms or current_epoch_ms > end_epoch_ms


def get_date_time_in_epoch_ms(date_time_str):
    tz = pytz.timezone("America/New_York")
    datetime_edt = datetime.fromisoformat(date_time_str)
    datetime_new_york = datetime_edt.astimezone(tz)
    print(datetime_edt)
    print(datetime_new_york)
    epoch_ms = int(datetime_new_york.timestamp()) * 1000
    print(epoch_ms)
    return epoch_ms


def epoch_ms_to_date_time_str(epoch_ms, tz_name="America/New_York"):
    tz = pytz.timezone(tz_name)
    dt = datetime.fromtimestamp(epoch_ms / 1000, tz=tz)
    return dt.isoformat()


def filter_slots_by_time_range(slots, start_epoch_ms, end_epoch_ms):
    filtered_slots = []
    for slot in slots:
        slot_epoch_ms = get_date_time_in_epoch_ms(slot)
        if start_epoch_ms <= slot_epoch_ms <= end_epoch_ms:
            filtered_slots.append(slot)
    return filtered_slots


def get_current_and_future_epoch_america_new_york_milliseconds(selected_slot=None):
    tz = pytz.timezone("America/New_York")

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
