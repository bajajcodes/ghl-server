import json
import os

import requests

gohighlevel_url = os.environ.get("GHL_API_URL")
calendarId = os.environ.get("GHL_CALENDAR_ID")
timezone = os.environ.get("GHL_CALENDAR_TIMEZONE")
ghl_token=os.environ.get("GHL_BEARER_TOKEN")
headers = {
  'Version': '2021-04-15',
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {ghl_token}'  
}

async def create_appointment(phone, selected_slot, logger):
  try:
      logger.info("selected_slot: {}".format(selected_slot))
      payload = json.dumps({
        "calendarId": calendarId,
        "selectedTimezone": timezone,
        "selectedSlot": selected_slot,
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
