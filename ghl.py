import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from utils import (
    filter_slots_by_time_range,
    get_current_and_future_epoch_america_new_york_milliseconds,
    get_current_date_america_new_york,
    get_first_and_third_slots,
)

load_dotenv()

gohighlevel_url = os.getenv("GHL_API_URL")
calendarId = os.getenv("GHL_CALENDAR_ID")
timezone = os.getenv("GHL_CALENDAR_TIMEZONE")
ghl_token = os.getenv("GHL_BEARER_TOKEN")
headers = {
    "Version": "2021-04-15",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ghl_token}",
}


# TODO: refactor code for maintainibility
async def create_appointment(appointment_data, logger):
    try:
        logger.info("selected_slot: {}".format(appointment_data["selected_slot"]))
        payload = json.dumps(
            {
                "calendarId": calendarId,
                "selectedTimezone": timezone,
                "selectedSlot": appointment_data["selected_slot"],
                "firstName": appointment_data["first_name"],
                "lastName": appointment_data["last_name"],
                "Phone to text": appointment_data["phone"],
                "phone": appointment_data["phone"],
            }
        )
        response = requests.post(gohighlevel_url, headers=headers, data=payload)
        response_data = response.json()
        selected_slot_data = response_data.get("selectedSlot", {})
        slot_message = selected_slot_data.get("message", "Something Went Wrong")
        rule = selected_slot_data.get("rule", "")
        if response.status_code == 200:
            logger.info(
                "Appointment created successfully. GoHighLevel API response: %s",
                response_data,
            )
            return {"result": "Appointment created successfully"}
        elif response.status_code == 422:
            if rule == "invalid":
                logger.warning(
                    "Slot not available. GoHighLevel API response: %s", response_data
                )
                available_slots_response = await fetch_available_slots(
                    selected_slot=appointment_data["selected_slot"], logger=logger
                )
                logger.info("Available Slots %s", available_slots_response)
                return [
                    {
                        "error": "Requested slot {} is already booked".format(
                            appointment_data["selected_slot"]
                        )
                    },
                    {"result": available_slots_response},
                ]
            elif rule == "iso8601":
                logger.warning(
                    "Invalid slot format. GoHighLevel API response: %s", response_data
                )
                return {"error": "Date Time"}
            else:
                logger.error(
                    "Unprocessable Entity from GoHighLevel API: %s", response_data
                )
                return {"error": "Something Went Wrong"}
        else:
            # Handle other unexpected responses
            logger.error(
                "Unexpected GoHighLevel API response (status %s): %s",
                response.status_code,
                response_data,
            )
            return [
                {"error": "Sorry we cannot book your Appointment, please try later."}
            ]
    except requests.RequestException as e:
        logger.error(f"Error creating appointment on GoHighLevel: {e}")
        raise  # Re-raise the exception so it can be handled further


async def fetch_available_slots(selected_slot, logger):

    try:
        start_epoch, end_epoch = (
            get_current_and_future_epoch_america_new_york_milliseconds(selected_slot)
        )
        url = f"{gohighlevel_url}/slots?calendarId={calendarId}&startDate={start_epoch}&endDate={end_epoch}&timezone=America/New_York"
        headers = {"Authorization": f"Bearer {ghl_token}"}

        logger.info(f"Fetching slots from: {url}")  # Log the request URL

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            today = get_current_date_america_new_york()
            slots = data.get(today, {}).get("slots", [])
            logger.info(
                "Today date available for {} and slots are {}".format(today, slots)
            )
            # if selected_slot is not provided don't filter slots
            time_range_filtered_slots = (
                filter_slots_by_time_range(
                    slots=slots, start_epoch_ms=start_epoch, end_epoch_ms=end_epoch
                )
                if selected_slot
                else slots
            )
            logger.info(
                "Today(Time Range Filtered slots) date available for {} and slots are {}".format(
                    today, time_range_filtered_slots
                )
            )
            if today in data:
                if time_range_filtered_slots:
                    filtered_slots = get_first_and_third_slots(
                        slots=time_range_filtered_slots
                    )
                    logger.info(
                        f"Successfully fetched slots: {filtered_slots}"
                    )  # Log the fetched slots
                    return {
                        "result": "Available slots",
                        "available_slots": filtered_slots,
                    }
            # This else block is for both cases: no data for today OR empty slots list
            logger.info("No slots available for today")
            return {"result": "No Available slots", "available_slots": []}
        else:
            error_msg = (
                f"Error fetching slots: {response.status_code} - {response.text}"
            )
            logger.error(error_msg)
            return {"error": "No Available slots", "available_slots": []}

    except requests.RequestException as e:
        logger.exception(
            "RequestException while fetching slots:", exc_info=True
        )  # Log the exception with traceback
        raise  # Re-raise the exception to let the caller handle it

    except KeyError as e:
        logger.exception(
            "KeyError while extracting slots from response:", exc_info=True
        )
        raise  # Re-raise the exception

    except Exception as e:  # Catch any other unexpected exceptions
        logger.exception("Unexpected error while fetching slots:", exc_info=True)
        raise
