import os

from dotenv import load_dotenv
from openai import OpenAI

from prompts import SYSTEM_PROMPT, USER_PROMPT
from utils import get_current_time_america_new_york, replace_placeholders

load_dotenv() 

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# openai.api_key=os.environ.get("OPENAI_API_KEY")
client = OpenAI()

async def create_chat_completion(user_message, logger):
    now = get_current_time_america_new_york()
    logger.info("Current Time: %s", now)
    final_prompt = replace_placeholders(USER_PROMPT, now, user_message)
    logger.info("Sending request to OpenAI API. Final prompt: %s", final_prompt)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": final_prompt},
            ],
            temperature=0,
        )
    except RuntimeError as e:
        logger.error("OpenAI API Error: %s", e)
        raise  # Re-raise the exception so it can be handled further

    logger.info("Received response from OpenAI API")
    return response.choices[0].message.content