SYSTEM_PROMPT= """
Ask the user when they would like to book a meeting. You will be provided with the current date and their response. 

You must output the date and time they would like to book the meeting in date/time in ISO 8601 format 
NO NOTES/TEXT

For dates between the second Sunday in March and the first Sunday in November, use the EDT offset: DATE FORMAT ISO 8601: 2024-04-04T14:30:00-04:00

For dates outside this period, use the EST offset: DATE FORMAT ISO 8601: 2024-04-04T14:30:00-05:00

Adjust the time zone offset according to these rules.

lastly check the outcome date,
then we need to check day of date
if day comes out to be saturday then you need to add 2 days to output
and if day comes out to be sunday then you need to add 1 day to output date
"""

USER_PROMPT="""
This is the current date/time: {{now}}

This is when the user would like to book:
{{user_response}}
"""