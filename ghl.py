import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from utils import get_current_and_future_epoch_america_new_york_milliseconds

load_dotenv()

gohighlevel_url = os.getenv("GHL_API_URL")
calendarId = os.getenv("GHL_CALENDAR_ID")
timezone = os.getenv("GHL_CALENDAR_TIMEZONE")
ghl_token=os.getenv("GHL_BEARER_TOKEN")
headers = {
  'Version': '2021-04-15',
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {ghl_token}'  
}

async def create_appointment(phone, full_name, selected_slot, logger):
  try:
      logger.info("selected_slot: {}".format(selected_slot))
      payload = json.dumps({
        "calendarId": calendarId,
        "selectedTimezone": timezone,
        "selectedSlot": selected_slot,
        "fullName": full_name,
        "phone": phone
      })
      response = requests.post(gohighlevel_url, headers=headers, data=payload)
      response_data = response.json() 
      selected_slot_data = response_data.get("selectedSlot", {})  
      slot_message = selected_slot_data.get("message", "") 
      rule = selected_slot_data.get("rule", "")
      if response.status_code == 200:
            logger.info("Appointment created successfully. GoHighLevel API response: %s", response_data)
            return {"message": "Appointment created successfully"}
      elif response.status_code == 422:
            if rule == "invalid":
                logger.warning("Slot not available. GoHighLevel API response: %s", response_data)
                return {"message": slot_message}
            elif rule == "iso8601":
                logger.warning("Invalid slot format. GoHighLevel API response: %s", response_data)
                return {"message": slot_message}
            else: 
                logger.error("Unprocessable Entity from GoHighLevel API: %s", response_data)
                return {"message": "Unprocessable Entity"}
      else:
            # Handle other unexpected responses
            logger.error("Unexpected GoHighLevel API response (status %s): %s", response.status_code, response_data)
            return {"message": "Sorry we cannot book your Appointment, please try later."}
  except requests.RequestException as e:
        logger.error(f"Error creating appointment on GoHighLevel: {e}")
        raise  # Re-raise the exception so it can be handled further

async def fetch_available_slots(logger):

    try:
        start_epoch, end_epoch = get_current_and_future_epoch_america_new_york_milliseconds()
        url = f"{gohighlevel_url}/slots?calendarId={calendarId}&startDate={start_epoch}&endDate={end_epoch}&timezone=America/New_York"
        headers = {'Authorization': f'Bearer {ghl_token}'}

        logger.info(f"Fetching slots from: {url}")  # Log the request URL

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            today = datetime.now().strftime("%Y-%m-%d")
            slots = data.get(today, {}).get("slots", [])
            logger.info(f"Successfully fetched slots: {slots[:2]}")  # Log the fetched slots
            return {"message": "Available slots", "available_slots": slots[:2]}
        else:
            error_msg = f"Error fetching slots: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {"message": "No Available slots", "available_slots": []}  

    except requests.RequestException as e:
        logger.exception("RequestException while fetching slots:", exc_info=True)  # Log the exception with traceback
        raise  # Re-raise the exception to let the caller handle it

    except KeyError as e:
        logger.exception("KeyError while extracting slots from response:", exc_info=True)
        raise  # Re-raise the exception

    except Exception as e:  # Catch any other unexpected exceptions
        logger.exception("Unexpected error while fetching slots:", exc_info=True)
        raise

