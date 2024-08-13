from datetime import datetime, timedelta
from openai import AsyncOpenAI
import os
from database import session_scope, Message, UserEngagement, TranscriptSummary
from shared_utils import logger, log_info, log_error, log_warning

async def generate_response_with_openai(prompt):
    logger.info(f"Prompt being sent to OpenAI: {prompt}")
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = await client.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        log_error(f"Error generating response from OpenAI: {e}")
        return "An error occurred while generating the response."

async def process_message_with_context(prompt, user_id, platform, conversation_id):
    # Implement this function to process messages with context
    return await generate_response_with_openai(prompt)

def get_relevant_summary(user_id):
    # Implement this function to get relevant summary for a user
    return "No summary available"

async def save_message(content, platform, user_id, username):
    async with session_scope() as session:
        message = Message(
            content=content,
            platform=platform,
            user_id=user_id,
            username=username
        )
        session.add(message)
        await session.commit()