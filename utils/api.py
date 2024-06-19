from datetime import datetime, time, timedelta

import pytz
from fastapi import HTTPException, Request

from ghl_cls import GoHighLevelClient
from utils.ghl import datetime_str_to_epoch_ms, get_first_slots, get_next_business_day


def parse_datetime_string(datetime_str):
    """Parses a datetime string with ISO 8601 format and returns a datetime object."""

    try:
        # Use ISO 8601 format for parsing
        parsed_datetime = datetime.fromisoformat(datetime_str)
        now_edt = datetime.now(pytz.timezone("America/New_York"))
        # Localize the parsed datetime to EDT (if it doesn't have a timezone)
        if parsed_datetime.tzinfo is None:
            parsed_datetime = pytz.timezone("America/New_York").localize(
                parsed_datetime
            )

        # Compare in EDT timezone
        # INFO: dependant on internal python comparison, didn't checked their algos
        if parsed_datetime < now_edt:
            return now_edt
        else:
            return parsed_datetime
    except ValueError:
        raise ValueError(
            "Invalid datetime string format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS[-|+]ZZ)."
        )


# Extract request data and validation logic
async def process_request(request: Request):
    """
    Processes the incoming request, extracts relevant data, and performs validation.

    Args:
        request (Request): The incoming FastAPI Request object.

    Returns:
        dict: The first tool call dictionary from the request body.

    Raises:
        HTTPException: If the request body is missing or has an invalid format.
    """
    request_body = await request.json()
    message = request_body.get("message", {})
    tool_calls = message.get("toolCalls", [])

    if not tool_calls:
        raise HTTPException(
            status_code=400,
            detail="Invalid request format: missing 'message' or 'toolCalls'",
        )

    return tool_calls[0]  # Assuming only the first tool call is relevant


# Handle slot fetching and processing
async def fetch_and_process_slots(current_datetime_edt, edt_timezone, days=1):
    start_date = get_next_business_day(current_datetime_edt, is_start_date=True)
    next_day_end_time = edt_timezone.localize(
        datetime.combine(start_date.date() + timedelta(days=days), time(17, 0))
    )
    end_date = get_next_business_day(next_day_end_time, is_start_date=False)
    # print(
    #     f"start_date: {start_date} next_day_end_time:{next_day_end_time} end_date: {end_date}"
    # )
    formatted_start_date = (
        start_date.strftime("%Y-%m-%d %H:%M:%S")
        + start_date.strftime("%z")[:3]
        + ":"
        + start_date.strftime("%z")[3:]
    )
    formatted_end_date = (
        end_date.strftime("%Y-%m-%d %H:%M:%S")
        + end_date.strftime("%z")[:3]
        + ":"
        + end_date.strftime("%z")[3:]
    )
    # print(
    #     f"formatted_start_date: {formatted_start_date} formatted_end_date: {formatted_end_date}"
    # )
    start_epoch_ms = datetime_str_to_epoch_ms(formatted_start_date)
    end_epoch_ms = datetime_str_to_epoch_ms(formatted_end_date)
    # print(f"start_epoch_ms {start_epoch_ms} end_epoch_ms  {end_epoch_ms}")
    ghl = GoHighLevelClient()
    result, status_code = await ghl.get_appointment_slots(start_epoch_ms, end_epoch_ms)

    if status_code != 200:
        raise HTTPException(
            status_code=status_code, detail=result
        )  # Use more specific exceptions
    # print(f"result: {result}")
    slots = get_first_slots(result, formatted_start_date)
    if len(slots) < 2:
        return await fetch_and_process_slots(
            current_datetime_edt=current_datetime_edt, edt_timezone=edt_timezone, days=2
        )
    # print(f"slots: {slots}")
    picked_slots = [item[1] for item in slots]
    return picked_slots


def get_current_time_america_new_york():
    tz = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")


def replace_placeholders(prompt, now, user_response):
    prompt = prompt.replace("{{now}}", now)
    prompt = prompt.replace("{{user_response}}", user_response)
    return prompt
