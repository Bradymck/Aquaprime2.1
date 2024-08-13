import logging
from datetime import datetime, timedelta
from openai import AsyncOpenAI  # Use AsyncOpenAI
import os
from database import session_scope, Message, UserEngagement, TranscriptSummary  # Add this import

# Set up logger
logger = logging.getLogger('UnifiedBot')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_info(message):
    logger.info(message)

def log_success(message):
    logger.info(message)

def log_warning(message):
    logger.warning(message)

def log_error(message):
    logger.error(message)

async def generate_response_with_openai(prompt):
    logger.info(f"Prompt being sent to OpenAI: {prompt}")
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Use AsyncOpenAI

    try:
        response = await client.Completion.create(
            engine="gpt-3.5-turbo-instruct",  # Updated to use the instruct model
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        log_error(f"Error generating response from OpenAI: {e}")
        return "An error occurred while generating the response."

async def process_message_with_context(prompt, user_id, platform, conversation_id):
    # Implement this function to process messages with context
    # This is a placeholder implementation
    return await generate_response_with_openai(prompt)

def get_relevant_summary(user_id):
    # Implement this function to get relevant summary for a user
    # This is a placeholder implementation
    return "No summary available"

async def save_message(content, platform, user_id, username):
    async with session_scope() as session:
        message = Message(
            content=content,
            platform=platform,
            user_id=user_id,
            username=username,
            sentiment=analyze_sentiment(content)
        )
        session.add(message)
        await session.flush()

        # Update user engagement
        user_engagement = await session.get(UserEngagement, user_id)
        if not user_engagement:
            user_engagement = UserEngagement(user_id=user_id, username=username)
            session.add(user_engagement)

        user_engagement.message_count += 1
        user_engagement.overall_sentiment = (user_engagement.overall_sentiment * (user_engagement.message_count - 1) + message.sentiment) / user_engagement.message_count
        user_engagement.last_active = datetime.utcnow()

def update_user_reputations():
    with session_scope() as session:
        users = session.query(UserEngagement).all()
        for user in users:
            if (datetime.utcnow() - user.last_active) <= timedelta(days=7):
                user.reputation += 1
            if user.overall_sentiment > 0.5:
                user.reputation += 2
            elif user.overall_sentiment < -0.5:
                user.reputation -= 1
            user.reputation = max(0, min(user.reputation, 100))
    logger.info("User reputations updated")

def purge_old_messages(days_to_keep=30):
    with session_scope() as session:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted = session.query(Message).filter(Message.created_at < cutoff_date).delete()
        logger.info(f"Purged {deleted} messages older than {days_to_keep} days")

async def periodic_summarization(agent_id, api_key, user_id):
    # This function should be implemented to periodically create summaries
    # of recent conversations and store them in the TranscriptSummary table
    pass

async def summarize_transcripts(transcripts):
    # This function should be implemented to create summaries from the provided transcripts
    pass

def analyze_sentiment(content):
    # Implement a simple sentiment analysis function
    # This is a placeholder implementation, you might want to use a more sophisticated method
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing', 'poor']

    words = content.lower().split()
    sentiment = sum(word in positive_words for word in words) - sum(word in negative_words for word in words)
    return sentiment / len(words) if words else 0

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())