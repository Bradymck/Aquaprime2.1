import logging
from datetime import datetime, timedelta
from database import session_scope, UserEngagement, Message, TranscriptSummary
from textblob import TextBlob
from openai import AsyncOpenAI
import os

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

async def generate_response_with_openai(prompt):
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error communicating with OpenAI API: {str(e)}")
        if 'invalid_api_key' in str(e):
            logger.error("Invalid API key. Please check your OpenAI API key in Replit secrets.")
        return "Sorry, I encountered an error while processing your request."

async def process_message_with_context(content, user_id, platform, conversation_id):
    with session_scope() as session:
        past_messages = session.query(Message).filter_by(user_id=user_id).order_by(Message.created_at.desc()).limit(5).all()
        past_messages = [msg.content for msg in past_messages]

        user = session.query(UserEngagement).filter_by(user_id=user_id).first()
        user_sentiment = user.overall_sentiment if user else 0.0

    ram_messages = " ".join(past_messages)

    prompt = (f"System Instructions: Handle the following user messages.\n"
              f"User Sentiment: {user_sentiment}\n"
              f"Platform: {platform}\n"
              f"Recent Context: {ram_messages}\n"
              f"User Message: {content}")

    ai_response = await generate_response_with_openai(prompt)
    return ai_response

async def save_message(content, platform, user_id, username):
    sentiment = analyze_sentiment(content)
    with session_scope() as session:
        new_message = Message(content=content, platform=platform, user_id=user_id, username=username, sentiment=sentiment)
        session.add(new_message)
        user = session.query(UserEngagement).filter_by(user_id=user_id).first()
        if user:
            user.message_count += 1
            user.last_active = datetime.utcnow()
            user.overall_sentiment = (user.overall_sentiment * (user.message_count - 1) + sentiment) / user.message_count
        else:
            new_user = UserEngagement(user_id=user_id, username=username, message_count=1, overall_sentiment=sentiment)
            session.add(new_user)
    logger.info(f"Message saved to database for user {username}")

def get_relevant_summary(user_id):
    with session_scope() as session:
        latest_summary = session.query(TranscriptSummary).order_by(TranscriptSummary.created_at.desc()).first()
        user = session.query(UserEngagement).filter_by(user_id=user_id).first()
        last_interaction = user.last_active if user else None

        if last_interaction and latest_summary and latest_summary.created_at > last_interaction:
            return latest_summary

        return session.query(TranscriptSummary).order_by(TranscriptSummary.created_at.desc()).first()

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
    # It should use the OpenAI API to generate summaries
    pass