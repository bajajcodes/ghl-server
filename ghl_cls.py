import os

import requests
from dotenv import load_dotenv

load_dotenv()


class GoHighLevelClient:

    def __init__(self):
        self.base_url = "https://rest.gohighlevel.com/v1/appointments/slots"
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

        url = f"{self.base_url}?calendarId={self.calendar_id}&startDate={start_date_epoch_ms}&endDate={end_date_epoch_ms}&timezone={self.timezone}"
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
