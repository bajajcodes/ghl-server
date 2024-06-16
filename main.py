import asyncio
import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ai import create_chat_completion
from ghl import create_appointment, fetch_available_slots

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create logger instance
logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
async def hello_world():
    return "Hello World"


@app.post("/webhook")
async def hello_webhook(request: Request):
    try:
        logger.info(
            f"Received POST request: method={request.method}, path={request.url.path}"
        )
    except:
        pass


@app.post("/")
async def fetchSlotsAndBookAppointment(request: Request):
    try:
        request_body = await request.json()

        # TODO: logger required details only
        logger.info(
            f"Received POST request: method={request.method}, path={request.url.path}, "
            f"body={request_body}"
        )
        tool_calls = request_body["message"]["toolCalls"]
        # TODO: check vapi use of 400 status code
        if not tool_calls:
            return JSONResponse(
                content={
                    "error": "Invalid request format: missing 'message' or 'toolCalls'"
                },
                status_code=400,
            )
        tool_call = tool_calls[0]

        # Extract data from the tool call
        tool_call_id = tool_call.get("id")

        function_arguments = tool_call.get("function", {}).get("arguments", {})
        user_selected_slot = function_arguments.get("userSelectedSlot")
        user_suggested_slot = function_arguments.get("userSuggestedSlot")
        selected_slot = (
            user_selected_slot if user_selected_slot else user_suggested_slot
        )
        mobile_number = function_arguments.get("mobileNumber")
        first_name = function_arguments.get("firstName")
        last_name = function_arguments.get("lastName")

        if selected_slot and user_suggested_slot:
            selected_slot = await create_chat_completion(selected_slot, logger)

        # TODO: make the code readable and maintainable
        if selected_slot:

            logger.info(
                "User Info: %s",
                {
                    "mobile_number": mobile_number,
                    "first_name": first_name,
                    "last_name": last_name,
                    "selected_slot": selected_slot,
                    "user_selected_slot": user_selected_slot,
                    "user_suggested_slot": user_suggested_slot,
                },
            )  # Log user info as a dictionary

            scheduled_appointment_response = await create_appointment(
                {
                    "phone": mobile_number,
                    "first_name": first_name,
                    "last_name": last_name,
                    "selected_slot": selected_slot,
                },
                logger,
            )

            logger.info(
                "Appointment Response: %s", scheduled_appointment_response
            )  # Log the entire response

            # Extract message and available_slots safely (with defaults)
            appointment_message = scheduled_appointment_response.get(
                "message", "Something Went Wrong"
            )
            available_slots = scheduled_appointment_response.get("available_slots", [])

            logger.info("Slots: %s Message: %s", available_slots, appointment_message)

            formatted_response = {
                "results": [
                    {
                        "toolCallId": tool_call_id,
                        "result": (
                            available_slots if available_slots else appointment_message
                        ),
                    }
                ]
            }
            logger.info("Formatted Response: %s", formatted_response)

            # TODO: check vapi support for 4xx status codes
            return JSONResponse(content=formatted_response, status_code=200)

        available_slots_response = await fetch_available_slots(
            logger=logger, selected_slot=None
        )
        available_slots = available_slots_response["available_slots"]
        available_slots_message = available_slots_response["message"]
        formatted_response = {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": (
                        available_slots if available_slots else available_slots_message
                    ),
                }
            ]
        }
        logger.info(formatted_response)
        # TODO: check vapi support for 4xx status codes
        return JSONResponse(content=formatted_response, status_code=200)
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=3001)
