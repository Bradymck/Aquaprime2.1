from datetime import datetime, timedelta
from openai import AsyncOpenAI
import os
from database import session_scope, Message, UserEngagement, TranscriptSummary
from shared_utils import logger, log_info, log_error

async def generate_response_with_openai(prompt):
    logger.info(f"Prompt being sent to OpenAI: {prompt}")
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log_error(f"Error generating response from OpenAI: {e}")
        return "An error occurred while generating the response."

async def process_message_with_context(prompt, user_id, platform, conversation_id):
    # Implement the logic to process the message with context
    # For now, we'll use the generate_response_with_openai function
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