import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
from fastapi import HTTPException


class GoHighLevelClient:

    def __init__(self):
        self.base_url = "https://rest.gohighlevel.com/v1"
        self.calendar_id = os.getenv("CALENDAR_ID")
        self.timezone = os.getenv("TIMEZONE", "America/New_York")
        self.auth_token = os.getenv("AUTH_TOKEN")

    async def get_appointment_slots(self, start_date_epoch_ms, end_date_epoch_ms):
        """
        Fetches appointment slots from GoHighLevel API, handling missing configuration.

        Args:
            start_date_epoch_ms: Start date in epoch milliseconds.
            end_date_epoch_ms: End date in epoch milliseconds.

        Returns:
            tuple: A tuple containing the result and status code of the API request.

            - If successful (200 OK): (slot_data_dict, 200)
            - If client error (4xx): (error_message, status_code)
            - If server error (5xx): ("Internal Server Error", 500)
            - If configuration missing: ("Missing Configuration (CALENDAR_ID or AUTH_TOKEN)", None)
            - If unexpected error: ("Unknown Error", None)
        """

        # Check if calendar_id and auth_token are available
        if not self.calendar_id or not self.auth_token:
            return "Missing Configuration (CALENDAR_ID or AUTH_TOKEN)", None

        url = f"{self.base_url}/appointments/slots?calendarId={self.calendar_id}&startDate={start_date_epoch_ms}&endDate={end_date_epoch_ms}&timezone={self.timezone}"
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:  # Success
                return response.json(), response.status_code
            elif 400 <= response.status_code < 500:  # Client error
                error_data = response.json()
                if "msg" in error_data:
                    return error_data["msg"], response.status_code
                else:
                    return "Bad Request", response.status_code
            elif response.status_code >= 500:  # Server error
                return "Internal Server Error", response.status_code
            else:  # Unexpected error
                return "Unknown Error", None

        except requests.RequestException as e:
            print(f"Request Error: {e}")
            return "Request Error", None

    async def check_slot_bookable(
        self, firstName, lastName, phone, phoneToText, selectedSlot
    ):
        """
        Checks if a specific appointment slot is bookable and books the slot if available.

        Args:
            firstName (str): First name of the contact.
            lastName (str): Last name of the contact.
            phone (str): Phone number of the contact.
            phoneToText (str): "Phone" to send SMS, or "Email" to send email.
            selectedSlot (str): The selected slot in ISO 8601 format.

        Returns:
            tuple: (booking_result, status_code) where:
                - booking_result (dict): API response data if successful, or an error message.
                - status_code (int): HTTP status code of the response.
        """
        # Get calendarId and selectedTimezone from environment variables if not provided
        calendar_id = os.getenv("CALENDAR_ID")
        selected_timezone = os.getenv("TIMEZONE", "America/New_York")

        # Check if calendarId and selectedTimezone are available in environment variables
        if not calendar_id or not selected_timezone:
            raise HTTPException(
                status_code=500,
                detail="Calendar ID or selected timezone is missing in environment variables.",
            )

        # Input validation (Simplified)
        payload_fields = {
            "calendarId": calendar_id,
            "selectedTimezone": selected_timezone,
            "selectedSlot": selectedSlot,
            "phone": phone,
            "Phone to text": phoneToText,
            "firstName": firstName,
            "lastName": lastName,
        }
        missing_fields = [field for field, value in payload_fields.items() if not value]

        if missing_fields:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required fields: {', '.join(missing_fields)}",
            )

        url = f"{self.base_url}/appointments"
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        payload = json.dumps(
            {key: value for key, value in payload_fields.items() if value}
        )

        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code == 200:  # Success
                success_data = response.json()
                return "Slot booked succesfully", response.status_code
            elif response.status_code == 422:
                error_data = response.json()
                missing_fields = [
                    field
                    for field in ["calendarId", "selectedTimezone", "phone"]
                    if field in error_data
                ]
                if "selectedSlot" in error_data:
                    return error_data["selectedSlot"]["message"], 422
                elif missing_fields:
                    return f"Missing required fields: {', '.join(missing_fields)}", 422
            else:  # Unexpected error
                return "Unknown Error", None

        except requests.RequestException as e:
            print(f"Request Error: {e}")
            return "Request Error", None
