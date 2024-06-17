import logging
from datetime import datetime

import pytz
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from ghl_cls import GoHighLevelClient
from utils.api import fetch_and_process_slots, process_request

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
    try:
        tool_call = await process_request(request)
        tool_call_id = tool_call.get("id")

        edt_timezone = pytz.timezone("America/New_York")
        current_datetime_edt = datetime.now(edt_timezone)

        picked_slots = await fetch_and_process_slots(current_datetime_edt, edt_timezone)
        # TODO: send message and available_slots in result
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
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions to be handled by FastAPI
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)


@app.post("/bookslot")
async def bookSlot(request: Request):
    try:
        # 1. Extract and validate request data
        tool_call = await process_request(request)
        tool_call_id = tool_call.get("id")
        function_arguments = tool_call.get("function", {}).get("arguments", {})

        # 2. Extract appointment details
        appointment_details = {
            "selectedSlot": function_arguments.get("selectedSlot"),
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

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=3000)
