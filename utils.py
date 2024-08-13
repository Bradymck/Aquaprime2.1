import asyncio
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_generate_response(prompt):
    return asyncio.run(generate_response_with_openai(prompt))

async def generate_response_with_openai(prompt):
    cached_response = cached_generate_response(prompt)
    if cached_response:
        return cached_response

    logger.info(f"Prompt being sent to OpenAI: {prompt}")
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
        cached_generate_response.cache_clear()  # Clear cache periodically to avoid stale responses
        return response.choices[0].message.content.strip()
    except Exception as e:
        log_error(f"Error generating response from OpenAI: {e}")
        return "An error occurred while generating the response."

async def process_message_with_context(prompt, user_id, platform, conversation_id):
    context = await get_relevant_context(user_id, platform, conversation_id)
    full_prompt = f"{context}\n\nUser: {prompt}\n\nAI:"
    return await generate_response_with_openai(full_prompt)

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

async def save_message(content, platform, user_id, username, is_user=True):
    async with session_scope() as session:
        message = Message(
            content=content,
            platform=platform,
            user_id=user_id,
            username=username,
            is_user=is_user
        )
        session.add(message)
        await session.commit()