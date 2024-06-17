import logging
from datetime import datetime

import pytz
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from chat_gpt_agent import ChatGPTAgent, user_message
from ghl_cls import GoHighLevelClient
from utils.api import (
    fetch_and_process_slots,
    get_current_time_america_new_york,
    process_request,
    replace_placeholders,
)

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
    pass


@app.post("/fetchslots")
async def fetchSlots(request: Request):
    tool_call_id = None
    try:
        # Process request and get slots
        tool_call = await process_request(request)
        tool_call_id = tool_call.get("id")
        edt_timezone = pytz.timezone("America/New_York")
        current_datetime_edt = datetime.now(edt_timezone)
        picked_slots = await fetch_and_process_slots(current_datetime_edt, edt_timezone)
        # Success response
        return JSONResponse(
            content={
                "results": [
                    {
                        "toolCallId": tool_call_id,
                        "result": {
                            "message": "The following slots are available",
                            "available_slots": picked_slots,
                        },
                    }
                ]
            },
            status_code=200,
        )
    except HTTPException as he:  # Catch specific HTTPException
        logger.critical(f"An HTTPException occurred: {he}")
        return JSONResponse(
            content={
                "results": [{"toolCallId": None, "error": {"message": he.detail}}]
            },
            status_code=he.status_code,
        )
    except Exception as e:  # Catch all other exceptions
        logger.critical(f"An unexpected error occurred: {e}")
        error_message = (
            "Something went wrong while fetching slots."
            if tool_call_id
            else "Internal Server Error"
        )
        status_code = 200 if tool_call_id else 500
        return JSONResponse(
            content={
                "results": [
                    {"toolCallId": tool_call_id, "error": {"message": error_message}}
                ]
            },
            status_code=status_code,
        )


@app.post("/bookslot")
async def bookSlot(request: Request):
    tool_call_id = None
    try:
        # 1. Extract and validate request data
        tool_call = await process_request(request)
        tool_call_id = tool_call.get("id")
        function_arguments = tool_call.get("function", {}).get("arguments", {})

        selected_slot_str = function_arguments.get("selectedSlot")
        current_time_str = get_current_time_america_new_york()
        final_user_prompt = replace_placeholders(
            user_message, current_time_str, selected_slot_str
        )
        selected_slot_success, selected_slot = await ChatGPTAgent().extract_date_time(
            final_user_prompt
        )

        if not selected_slot_success:
            return JSONResponse(
                content={
                    "results": [
                        {
                            "toolCallId": tool_call_id,
                            "result": {"message": selected_slot},
                        }
                    ]
                },
                status_code=400,
            )

        # 2. Extract appointment details
        appointment_details = {
            "selectedSlot": selected_slot,
            "firstName": function_arguments.get("firstName"),
            "lastName": function_arguments.get("lastName"),
            "phone": function_arguments.get("phone"),
            "phoneToText": function_arguments.get("phone"),
        }

        # 3. Book appointment
        ghl_client = GoHighLevelClient()
        result, status_code = await ghl_client.check_slot_bookable(
            **appointment_details
        )

        # 4. Construct and return response
        if status_code == 200:
            message = "Appointment booked successfully."
        else:
            message = result  # Use the API error message directly

        return JSONResponse(
            content={
                "results": [
                    {
                        "toolCallId": tool_call_id,
                        "result": {"message": message},
                    }
                ]
            },
            status_code=status_code,
        )

    except HTTPException as he:  # Catch specific HTTPException
        logger.critical(f"An HTTPException occurred: {he}")
        return JSONResponse(
            content={
                "results": [{"toolCallId": None, "error": {"message": he.detail}}]
            },
            status_code=he.status_code,
        )
    except Exception as e:  # Catch all other exceptions
        logger.critical(f"An unexpected error occurred: {e}")
        error_message = (
            "Something went wrong when booking slot."
            if tool_call_id
            else "Internal Server Error"
        )
        status_code = 200 if tool_call_id else 500
        return JSONResponse(
            content={
                "results": [
                    {"toolCallId": tool_call_id, "error": {"message": error_message}}
                ]
            },
            status_code=status_code,
        )


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=3000)
