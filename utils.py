import asyncio
from functools import lru_cache
from openai import AsyncOpenAI
import os
from shared_utils import logger, log_error
from database import session_scope, Message
from sqlalchemy import select
from datetime import datetime
import json
from game_state_manager import GameStateManager  # Added this import statement

@lru_cache(maxsize=100)
async def cached_generate_response(prompt):
    return await generate_response_with_openai(prompt)

async def generate_response_with_openai(prompt):
    cleaned_prompt = prompt.replace('\n', ' ').replace('  ', ' ')
    logger.info(f"Cleaned prompt being sent to OpenAI: {cleaned_prompt[:1000]}...")  # Log the first 1000 characters of the cleaned prompt
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log_error(f"Error generating response from OpenAI: {e}")
        return "An error occurred while generating the response."

async def process_message_with_context(prompt, user_id, platform, conversation_id):
    context = await get_relevant_context(user_id, platform, conversation_id)
    game_state_manager = GameStateManager("./AquaPrimeLORE", "./AquaPrimeLORE/game_state.json")
    game_state = game_state_manager.load_game_state()
    full_prompt = f"{context}\n\nGame State: {json.dumps(game_state, indent=2)}\n\nUser: {prompt}\n\nAI:"
    logger.info(f"Full prompt being sent to OpenAI:\n{full_prompt[:1000]}...")  # Log the first 1000 characters of the prompt
    return await cached_generate_response(full_prompt)

async def save_message(content, platform, user_id, username, is_user=True):
    async with session_scope() as session:
        message = Message(
            content=content,
            platform=platform,
            user_id=user_id,
            username=username,
            is_user=is_user,
            timestamp=datetime.utcnow()
        )
        session.add(message)

async def get_relevant_context(user_id, platform, conversation_id):
    async with session_scope() as session:
        recent_messages = await session.execute(
            select(Message)
            .filter(Message.user_id == user_id, Message.platform == platform)
            .order_by(Message.timestamp.desc())
            .limit(5)
        )
        recent_messages = recent_messages.scalars().all()
        
        context = "Previous conversation:\n"
        for msg in reversed(recent_messages):
            context += f"{'User' if msg.is_user else 'AI'}: {msg.content}\n"
        
        return context


async def get_relevant_summary(user_id, platform, conversation_id):
    # Implement summary retrieval logic here
    return "Relevant summary placeholder"