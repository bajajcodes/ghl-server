import os

import openai
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

system_message = """
Ask the user when they would like to book a meeting. You will be provided with the current date and their response.

You must output the date and time they would like to book the meeting in date/time in ISO 8601 format
AI assistant will not invent anything that is not drawn directly from the context. 
AI assistant will not output NOTES/TEXT, if done then penalize.
No NOTES/TEXT.

If the user only specifies a time (e.g., "morning," "afternoon," "2 PM"), assume it's for the current date.
If the user only specifies a date, assume they mean 8:00 AM on that date.

If the user specifies "morning," assume they mean 08:00 AM.
If the user specifies "afternoon," assume they mean 13:00 PM.
If the user specifies "evening," assume they mean 16:00 PM.

For dates between the second Sunday in March and the first Sunday in November, use the EDT offset: DATE FORMAT ISO 8601: 2024-04-04T14:30:00-04:00

For dates outside this period, use the EST offset: DATE FORMAT ISO 8601: 2024-04-04T14:30:00-05:00

Adjust the time zone offset according to these rules.

lastly check the outcome date,
then we need to check day of date
if day comes out to be saturday then you need to add 2 days to output
and if day comes out to be sunday then you need to add 1 day to output date
"""

user_message = """
This is the current date/time: {{now}}

This is when the user would like to book:
{{user_response}}
"""


class ChatGPTAgent:
    def __init__(self, model="gpt-4o"):
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment or passed in")

        self.openai_client = openai.AsyncOpenAI(api_key=self.api_key)
        self.model = model

    async def extract_date_time(self, user_input):
        """
        Extracts date and time information from user input using the OpenAI API.

        Args:
            system_message (str): The system message to guide the AI model.
            user_input (str): The user's input text.

        Returns:
            dict: A dictionary containing:
                - "success" (bool): True if the request was successful, False otherwise.
                - "message" (str): The AI model's response or an error message.
        """
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_input},
                ],
                temperature=0,
            )
            return True, response.choices[0].message.content
        except Exception as e:  # Catch all exceptions
            print(e)
            return False, "An error occurred while processing your request."
