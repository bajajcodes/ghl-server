from datetime import datetime, timezone

import pytz


def get_current_time_america_new_york():
    tz = pytz.timezone('America/New_York')
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")

def replace_placeholders(prompt, now, user_response):
    prompt = prompt.replace("{{now}}", now)
    prompt = prompt.replace("{{user_response}}", user_response)
    return prompt
