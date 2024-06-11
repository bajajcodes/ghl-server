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

@app.post("/")
async def process_request(request: Request):
    """
    Handles POST requests to the root route.
    Logs the request details and calls the create_chat_completion function.
    """
    request_body = await request.json()

    logger.info(
        f"Received POST request: method={request.method}, path={request.url.path}, "
        f"body={request_body}"
    )
    tool_calls = request_body["message"]["toolCalls"]
    # user_selected_slot = request_body.get("userSelectedSlot")
    # mobileNumber = request_body.get("mobileNumber")

    # Ensure 'message' and 'toolCalls' exist
    if not tool_calls:
        return JSONResponse(content={"error": "Invalid request format: missing 'message' or 'toolCalls'"}, status_code=400)
    tool_call = tool_calls[0]

    # Extract data from the tool call
    tool_call_id = tool_call.get("id")
    function_arguments = tool_call.get("function", {}).get("arguments", {})  # Safely access arguments
    mobile_number = function_arguments.get("mobileNumber")
    user_selected_slot = function_arguments.get("selectedSlot")

    # Log extracted data
    logger.info(f"Extracted data: toolCallId={tool_call_id}, mobileNumber={mobile_number}, selectedSlot={user_selected_slot}")

    if not user_selected_slot:
        return JSONResponse(
            content={"error": "Missing 'user_selected_slot' in request body"}, 
            status_code=400
        )

    try:
        selected_slot = await create_chat_completion(user_selected_slot, logger)
        logger.info(f"Received response from OpenAI API: {selected_slot}")
        scheduled_appointment_response = await create_appointment(mobile_number, selected_slot, logger)
        scheduled_appointment_response_message = scheduled_appointment_response["message"]
        formatted_response = {
        "results": [
            {
                "toolCallId": tool_call_id,
                "result": scheduled_appointment_response_message,
            }
        ]
        }
        return JSONResponse(
            content=formatted_response, 
            status_code=200
        )
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
        return JSONResponse(
            content={"error": "Internal Server Error"}, 
            status_code=500
        )

@app.post("/book")
async def fetchSlotsAndBookAppointment(request: Request):
    try:
        request_body = await request.json()

        logger.info(
                f"Received POST request: method={request.method}, path={request.url.path}, "
                f"body={request_body}"
        )
        tool_calls = request_body["message"]["toolCalls"]
        if not tool_calls:
            return JSONResponse(content={"error": "Invalid request format: missing 'message' or 'toolCalls'"}, status_code=400)
        tool_call = tool_calls[0]

        # Extract data from the tool call
        tool_call_id = tool_call.get("id")

        function_arguments = tool_call.get("function", {}).get("arguments", {})
        mobile_number = function_arguments.get("mobileNumber")
        user_selected_slot = function_arguments.get("selectedSlot")

        if user_selected_slot:
                    scheduled_appointment_response = await create_appointment(mobile_number, user_selected_slot, logger)
                    scheduled_appointment_response_message = scheduled_appointment_response["message"]
                    formatted_response = {
                    "results": [
                        {
                            "toolCallId": tool_call_id,
                            "result": scheduled_appointment_response_message,
                        }
                    ]
                    }
                    return JSONResponse(
                        content=formatted_response, 
                        status_code=200
                    )

        available_slots_response = await fetch_available_slots(logger)
        available_slots = available_slots_response["available_slots"]
        formatted_response = {
        "results": [
            {
                "toolCallId": tool_call_id,
                "result": available_slots,
            }
        ]
        }
        return JSONResponse(
            content=formatted_response, 
            status_code=200
        )
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
        return JSONResponse(
            content={"error": "Internal Server Error"}, 
            status_code=500
        )

# async def main():
#     try:
#         user_message = "Tomorrow Two PM"  # Example user message
#         response_content = await create_chat_completion(user_message, logger)
#         logger.info("Received response from OpenAI API, {}".format(response_content))
#     except Exception as e:  # Broad exception handling
#         logger.critical("An unexpected error occurred: %s", e)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=3000)
