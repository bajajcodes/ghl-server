from datetime import datetime, time, timedelta

import pytz


def get_first_slots(slot_data, current_datetime_str):
    """
    Extracts the first available slot with a 1-hour gap from the current datetime for the first key,
    and the first slot by default for the second key in the slot_data dictionary.

    Args:
        slot_data (dict): A dictionary containing dates as keys and slot lists as values.
        current_datetime_str (str): The current datetime in the format "YYYY-MM-DD HH:MM:SS-04:00" (EDT).

    Returns:
        list: A list of tuples where each tuple contains a date string and its first available slot.
    """

    first_slots = []
    edt_timezone = pytz.timezone("America/New_York")
    current_datetime = datetime.strptime(
        current_datetime_str, "%Y-%m-%d %H:%M:%S%z"
    ).astimezone(edt_timezone)

    key_count = 0  # Track the key index
    for date, slots_info in slot_data.items():
        if key_count == 0:  # First key
            found_slot = False
            for slot_str in slots_info["slots"]:
                try:
                    slot_datetime = datetime.strptime(
                        slot_str, "%Y-%m-%dT%H:%M:%S%z"
                    ).astimezone(edt_timezone)
                    if slot_datetime >= current_datetime + timedelta(hours=1):
                        first_slots.append((date, slot_str))
                        found_slot = True
                        break
                except ValueError:
                    print(f"Invalid slot format: {slot_str}")

            if (
                not found_slot and slots_info["slots"]
            ):  # Pick the last slot if no suitable slot found
                print(f"No slots available for date: {date}")
                first_slots.append((date, slots_info["slots"][-1]))

        elif key_count == 1:  # Second key
            if slots_info["slots"]:
                first_slots.append((date, slots_info["slots"][0]))
            else:
                print(f"No slots available for date: {date}")

        key_count += 1  # Increment the key counter

    return first_slots


def datetime_str_to_epoch_ms(datetime_str, timezone_str="America/New_York"):
    """
    Converts a datetime string in ISO 8601 format with timezone offset to epoch timestamp in milliseconds.

    Args:
        datetime_str: A string representing the date and time in ISO 8601 format (e.g., "2024-06-21 13:00:00-04:00").
        timezone_str: A string representing the timezone (default: 'America/New_York').

    Returns:
        int: The epoch timestamp in milliseconds, or None if the conversion fails.
    """
    try:
        # Parse the datetime string, including the timezone information
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S%z")
        # Get the specified timezone using pytz
        tz = pytz.timezone(timezone_str)
        if dt.tzinfo != tz:
            dt = dt.astimezone(tz)
        # Calculate the epoch timestamp in milliseconds
        epoch_timestamp_ms = int(dt.timestamp() * 1000)

        return epoch_timestamp_ms
    except ValueError as e:
        # Handle invalid datetime string format
        print(e)
        print(
            "Invalid datetime string format. Please use ISO 8601 format (e.g., '2024-06-21 13:00:00-04:00')."
        )
        return None


def is_within_business_hours(dt):
    """
    Checks if a datetime object is within business hours (8:00 AM - 5:00 PM EDT).

    Args:
        dt: A datetime object to check.

    Returns:
        bool: True if within business hours, False otherwise.
    """
    return dt.time() >= time(8, 0) and dt.time() <= time(17, 0)


def get_next_business_day(datetime_edt, is_start_date=True):
    """
    Takes a datetime object in EDT timezone and returns the next available business day,
    with time set to 8:00 AM for start dates and 5:00 PM for end dates.

    Args:
        datetime_edt: A datetime object representing the current time in EDT.
        is_start_date: A boolean indicating whether to return the start time (8:00 AM)
                       or end time (5:00 PM) of the next business day (default: True).

    Returns:
        datetime: A datetime object representing the next business day with appropriate time in EDT.
    """
    # Get EDT timezone using pytz
    edt_timezone = pytz.timezone("America/New_York")
    # TODO: check for both date and time if less than current date and time
    # INFO: temporarily removing current business hours logic
    #  is_within_business_hours(
    #     datetime_edt
    # )
    if datetime_edt.weekday() < 5:  # Weekday and within business hours
        return datetime_edt  # Return the current datetime as is
    else:
        # Calculate the next weekday
        days_until_next_weekday = (7 - datetime_edt.weekday()) % 7
        next_weekday = datetime_edt.date() + timedelta(days=days_until_next_weekday)

        # Set the time to 8:00 AM for sta   rt dates, 5:00 PM for end dates
        if is_start_date:
            return edt_timezone.localize(
                datetime.combine(next_weekday, time(8, 0))
            )  # 8:00 AM EDT
        else:
            return edt_timezone.localize(
                datetime.combine(next_weekday, time(17, 0))
            )  # 5:00 PM EDT
